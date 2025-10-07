"""
Main FastAPI Application - Production Grade
Clean, organized, and deployment-ready with comprehensive error handling and logging
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend to path for clean imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables first
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import production modules
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Import custom modules
from backend.config import (
    CORS_ORIGINS, API_PREFIX, LOG_LEVEL, SECRET_KEY, ENVIRONMENT,
    DATABASE_CONFIG, BASE_DIR
)
from backend.logging_config import setup_logging, get_logger
from backend.middleware import (
    exception_handler_middleware,
    logging_middleware,
    request_validation_middleware
)
from backend.exceptions import ValidationException
from backend.core import data_manager
from backend.routes import dashboard, forecast, recommended_order, sales_supervision

# Setup production-grade logging
log_dir = BASE_DIR / 'logs'
setup_logging(
    log_level=LOG_LEVEL,
    log_dir=log_dir,
    app_name='yaumi_analytics',
    json_logs=(ENVIRONMENT == 'production'),
    console_output=True
)

logger = get_logger(__name__)


def validate_environment():
    """Validate required environment variables on startup"""
    required_vars = ['DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.critical(error_msg)
        raise ValidationException(
            error_msg,
            details={'missing_variables': missing_vars}
        )

    logger.info("Environment validation successful")


# Validate environment on import
validate_environment()

import threading

# Background data loading
_data_loading_thread = None
_data_loading_complete = False


def load_data_in_background():
    """Load data in background thread (for synchronous operations)"""
    global _data_loading_complete

    try:
        logger.info("Background data loading started...")
        result = data_manager.initialize()

        if result['success']:
            logger.info("✓ Background data loading completed successfully")
            logger.info(f"  - Demand records: {result['data'].get('merged_demand_rows', 0):,}")
            logger.info(f"  - Customer records: {result['data'].get('customer_rows', 0):,}")
            logger.info(f"  - Journey records: {result['data'].get('journey_rows', 0):,}")
            logger.info(f"  - Date range: {result['data'].get('date_range', {})}")
            _data_loading_complete = True
        else:
            logger.error(f"✗ Background data loading failed: {result['errors']}")
            _data_loading_complete = False

    except Exception as e:
        logger.error(f"Error in background data loading: {e}", exc_info=True)
        _data_loading_complete = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with threaded data loading
    """
    global _data_loading_thread

    logger.info("="*70)
    logger.info("YAUMI ANALYTICS API - STARTING UP")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"API Version: 2.0.0")
    logger.info("="*70)

    try:
        # Start data loading in background thread (truly non-blocking)
        logger.info("Starting background data loading thread...")
        _data_loading_thread = threading.Thread(target=load_data_in_background, daemon=True)
        _data_loading_thread.start()

        logger.info("="*70)
        logger.info("YAUMI ANALYTICS API - READY")
        logger.info("Data is loading in background thread...")
        logger.info("="*70)

    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise

    yield

    # Cleanup on shutdown
    logger.info("="*70)
    logger.info("YAUMI ANALYTICS API - SHUTTING DOWN")
    logger.info("="*70)

    # Wait for background thread to complete (with timeout)
    if _data_loading_thread and _data_loading_thread.is_alive():
        logger.info("Waiting for background data loading thread to complete...")
        _data_loading_thread.join(timeout=10)
        if _data_loading_thread.is_alive():
            logger.warning("Background thread did not complete in time")

    # Close database pool
    from backend.database import get_database_manager
    db_manager = get_database_manager()
    db_manager.close_pool()

    logger.info("Cleanup completed successfully")

# Create FastAPI app with production configuration
app = FastAPI(
    title="Yaumi Analytics API",
    version="2.0.0",
    description="Professional Analytics Platform for Yaumi - Demand, Forecast, Recommendations & Supervision",
    lifespan=lifespan,
    docs_url="/api/docs" if ENVIRONMENT == 'development' else None,
    redoc_url="/api/redoc" if ENVIRONMENT == 'development' else None,
    openapi_url="/api/openapi.json" if ENVIRONMENT == 'development' else None,
)

# ============================================================================
# MIDDLEWARE STACK (Order matters - first added = outermost layer)
# ============================================================================

# 1. Exception Handler (outermost - catches all exceptions)
app.middleware("http")(exception_handler_middleware)

# 2. Request Logging
app.middleware("http")(logging_middleware)

# 3. Request Validation
app.middleware("http")(request_validation_middleware)

# 4. Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if ENVIRONMENT == 'production':
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'"
        )

    return response


# 5. GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 6. Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="yaumi_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=(ENVIRONMENT == 'production')
)

# 7. Trusted Host Protection (production only)
if ENVIRONMENT == 'production':
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.onrender.com", "*.vercel.app", "yaumi.com", "*.yaumi.com"]
    )

# 8. CORS Middleware (innermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=3600
)

# Include routers with clean prefixes
app.include_router(
    dashboard, 
    prefix=f"{API_PREFIX}/dashboard", 
    tags=["📊 Dashboard"]
)

app.include_router(
    forecast, 
    prefix=f"{API_PREFIX}/forecast", 
    tags=["📈 Forecast"]
)

app.include_router(
    recommended_order, 
    prefix=f"{API_PREFIX}/recommended-order", 
    tags=["🎯 Recommendations"]
)

app.include_router(
    sales_supervision,
    prefix=f"{API_PREFIX}/sales-supervision",
    tags=["👁️ Supervision"]
)

# Data refresh endpoint
@app.post(f"{API_PREFIX}/refresh-data")
async def refresh_data():
    """Reload all data from database"""
    try:
        logger.info("Manual data refresh triggered")
        result = data_manager.initialize()

        if result['success']:
            logger.info("Data refresh successful")
            return {
                "success": True,
                "message": "Data refreshed successfully",
                "data": {
                    "demand_records": result['data'].get('merged_demand_rows', 0),
                    "customer_records": result['data'].get('customer_rows', 0),
                    "journey_records": result['data'].get('journey_rows', 0)
                }
            }
        else:
            logger.error(f"Data refresh failed: {result['errors']}")
            return {
                "success": False,
                "message": "Data refresh failed",
                "errors": result['errors']
            }
    except Exception as e:
        logger.error(f"Error during data refresh: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint - API Information"""
    return {
        "name": "Yaumi Analytics API",
        "version": "2.0.0",
        "status": "running",
        "description": "Professional Analytics Platform",
        "endpoints": {
            "dashboard": f"{API_PREFIX}/dashboard",
            "forecast": f"{API_PREFIX}/forecast",
            "recommended_order": f"{API_PREFIX}/recommended-order",
            "sales_supervision": f"{API_PREFIX}/sales-supervision",
            "documentation": {
                "swagger": "/api/docs",
                "redoc": "/api/redoc"
            }
        }
    }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns service health status including database, data loading, and system info
    """
    from backend.database import get_database_manager
    from backend.config import validate_config
    import platform
    from datetime import datetime

    global _data_loading_complete, _data_loading_thread

    # Check data manager
    data_status = data_manager.get_summary()
    data_healthy = data_status.get('loaded', False)

    # Check background loading status
    loading_status = "complete" if _data_loading_complete else "in_progress"
    if _data_loading_thread and not _data_loading_thread.is_alive() and not _data_loading_complete:
        loading_status = "failed"

    # Check database
    db_manager = get_database_manager()
    db_health = db_manager.health_check()
    db_healthy = db_health.get('connected', False)

    # Check configuration
    config_validation = validate_config()
    config_healthy = config_validation.get('valid', False)

    # Overall health status - server is healthy even if data is still loading
    overall_healthy = db_healthy and config_healthy

    health_response = {
        "status": "healthy" if overall_healthy else "degraded",
        "service": "Yaumi Analytics API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connected": db_healthy,
                "message": db_health.get('message', ''),
                "pool_size": db_health.get('pool_size'),
                "current_connections": db_health.get('current_connections')
            },
            "data": {
                "status": "healthy" if data_healthy else ("loading" if loading_status == "in_progress" else "unhealthy"),
                "loaded": data_healthy,
                "loading_status": loading_status,
                "last_refresh": data_status.get('last_refresh'),
                "records": {
                    "demand": data_status.get('demand_records', 0),
                    "customer": data_status.get('customer_records', 0),
                    "journey": data_status.get('journey_records', 0)
                }
            },
            "configuration": {
                "status": "healthy" if config_healthy else "unhealthy",
                "valid": config_healthy,
                "issues": config_validation.get('issues', []),
                "warnings": config_validation.get('warnings', [])
            }
        },
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }
    }

    return health_response


@app.get(f"{API_PREFIX}/status")
async def api_status():
    """
    Detailed API status with data summary
    """
    data_summary = data_manager.get_summary()

    return {
        "service": "Yaumi Analytics API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "data": data_summary,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )