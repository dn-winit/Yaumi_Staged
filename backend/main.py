"""
Main FastAPI Application
Clean and organized with dynamic imports
"""

from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file from backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Validate required environment variables
required_env_vars = ['DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"WARNING: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add backend to path for clean imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration and modules
from backend.config import CORS_ORIGINS, API_PREFIX, LOG_LEVEL, LOG_FORMAT, SECRET_KEY, ENVIRONMENT
from backend.core import data_manager
from backend.routes import dashboard, forecast, recommended_order, sales_supervision

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Yaumi Analytics API...")
    
    # Initialize data manager on startup
    logger.info("Initializing data manager...")
    result = data_manager.initialize()
    
    if result['success']:
        logger.info(f"✓ Data loaded successfully")
        logger.info(f"  - Demand records: {result['data'].get('merged_demand_rows', 0)}")
        logger.info(f"  - Customer records: {result['data'].get('customer_rows', 0)}")
        logger.info(f"  - Journey records: {result['data'].get('journey_rows', 0)}")
    else:
        logger.error(f"✗ Data loading failed: {result['errors']}")
    
    yield
    logger.info("Shutting down Yaumi Analytics API...")

# Create FastAPI app
app = FastAPI(
    title="Yaumi Analytics API",
    version="2.0.0",
    description="Professional Analytics Platform for Yaumi - Demand, Forecast, Recommendations & Supervision",
    lifespan=lifespan,
    docs_url="/api/docs" if ENVIRONMENT == 'development' else None,  # Disable docs in production
    redoc_url="/api/redoc" if ENVIRONMENT == 'development' else None
)

# Security Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="yaumi_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=ENVIRONMENT == 'production'
)

# Trusted Host Protection (prevent host header attacks)
if ENVIRONMENT == 'production':
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.onrender.com", "*.vercel.app", "yaumi.com", "*.yaumi.com"]
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if ENVIRONMENT == 'production':
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

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
    """Health check endpoint"""
    data_status = data_manager.get_summary()
    return {
        "status": "healthy" if data_status.get('loaded') else "degraded",
        "service": "Yaumi Analytics API",
        "version": "2.0.0",
        "data_loaded": data_status.get('loaded', False),
        "last_refresh": data_status.get('last_refresh'),
        "records": {
            "demand": data_status.get('demand_records', 0),
            "customer": data_status.get('customer_records', 0),
            "journey": data_status.get('journey_records', 0)
        }
    }

@app.get(f"{API_PREFIX}/status")
async def api_status():
    """Detailed API status"""
    return data_manager.get_summary()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )