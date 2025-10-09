"""
Automatic Task Scheduler
Runs daily tasks automatically at configured times (Dubai timezone)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from functools import wraps
import pytz
import logging
import requests
import os
import time

from backend.constants.config_constants import (
    DEFAULT_SCHEDULER_TIMEZONE,
    DEFAULT_CRON_RECOMMENDATIONS_HOUR,
    DEFAULT_CRON_RECOMMENDATIONS_MINUTE,
    DEFAULT_CRON_CACHE_REFRESH_HOUR,
    DEFAULT_CRON_CACHE_REFRESH_MINUTE,
    DEFAULT_CRON_MAX_RETRIES,
    DEFAULT_CRON_RETRY_DELAY_SECONDS
)

logger = logging.getLogger(__name__)

# Get configuration from environment with defaults
SCHEDULER_TIMEZONE = os.getenv('SCHEDULER_TIMEZONE', DEFAULT_SCHEDULER_TIMEZONE)
CRON_RECOMMENDATIONS_HOUR = int(os.getenv('CRON_RECOMMENDATIONS_HOUR', str(DEFAULT_CRON_RECOMMENDATIONS_HOUR)))
CRON_RECOMMENDATIONS_MINUTE = int(os.getenv('CRON_RECOMMENDATIONS_MINUTE', str(DEFAULT_CRON_RECOMMENDATIONS_MINUTE)))
CRON_CACHE_REFRESH_HOUR = int(os.getenv('CRON_CACHE_REFRESH_HOUR', str(DEFAULT_CRON_CACHE_REFRESH_HOUR)))
CRON_CACHE_REFRESH_MINUTE = int(os.getenv('CRON_CACHE_REFRESH_MINUTE', str(DEFAULT_CRON_CACHE_REFRESH_MINUTE)))
CRON_MAX_RETRIES = int(os.getenv('CRON_MAX_RETRIES', str(DEFAULT_CRON_MAX_RETRIES)))
CRON_RETRY_DELAY_SECONDS = int(os.getenv('CRON_RETRY_DELAY_SECONDS', str(DEFAULT_CRON_RETRY_DELAY_SECONDS)))

# Timezone object
TZ = pytz.timezone(SCHEDULER_TIMEZONE)

# Global scheduler instance
scheduler = None


def retry_on_failure(max_retries=None, delay_seconds=None):
    """Retry decorator for cron jobs"""
    max_retries = max_retries or CRON_MAX_RETRIES
    delay_seconds = delay_seconds or CRON_RETRY_DELAY_SECONDS

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(
                            f"[RETRY] {func.__name__} failed (attempt {attempt}/{max_retries}), "
                            f"retrying in {delay_seconds}s: {e}"
                        )
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"[RETRY] {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
        return wrapper
    return decorator


@retry_on_failure()
def generate_daily_recommendations():
    """
    Generate recommendations for today (using configured timezone)
    Runs at configured time daily
    Generates for ALL routes automatically
    """
    try:
        # Get today's date in configured timezone
        tz_now = datetime.now(TZ)
        today = tz_now.strftime('%Y-%m-%d')

        api_url = os.getenv('API_URL', 'http://localhost:8000')

        logger.info(f"[CRON] Starting daily recommendation generation for {today} ({SCHEDULER_TIMEZONE})")

        url = f"{api_url}/api/v1/recommended-order/pre-generate-daily"
        params = {'date': today}

        response = requests.post(url, params=params, timeout=300)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"[CRON] ✓ {result.get('message')}")
                logger.info(
                    f"[CRON] ✓ Generated {result.get('records_saved', 0)} records "
                    f"across {result.get('routes_count', 0)} routes"
                )
            else:
                logger.warning(f"[CRON] ✗ {result.get('message')}")
        else:
            logger.error(f"[CRON] ✗ HTTP {response.status_code}")

        logger.info(f"[CRON] Completed daily generation for {today}")

    except Exception as e:
        logger.error(f"[CRON] Failed to generate daily recommendations: {e}")
        raise


@retry_on_failure(max_retries=2)
def refresh_in_memory_cache():
    """
    Refresh in-memory data cache
    Runs at configured time daily (after recommendation generation)
    """
    try:
        logger.info(f"[CRON] Starting daily cache refresh ({SCHEDULER_TIMEZONE})")

        from backend.core import data_manager

        result = data_manager.initialize()

        if result['success']:
            logger.info(
                f"[CRON] ✓ Cache refreshed successfully - "
                f"{result['data'].get('merged_demand_rows', 0)} demand records loaded"
            )
        else:
            logger.error(f"[CRON] ✗ Cache refresh failed: {result['errors']}")
            raise Exception(f"Cache refresh failed: {result['errors']}")

    except Exception as e:
        logger.error(f"[CRON] Failed to refresh cache: {e}")
        raise


def start_scheduler():
    """
    Start the background scheduler
    Runs jobs at configured times in configured timezone
    """
    global scheduler

    if scheduler is not None:
        logger.warning("[SCHEDULER] Scheduler already running")
        return

    try:
        # Create background scheduler with configured timezone
        scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)

        # Job 1: Generate daily recommendations
        scheduler.add_job(
            generate_daily_recommendations,
            trigger=CronTrigger(
                hour=CRON_RECOMMENDATIONS_HOUR,
                minute=CRON_RECOMMENDATIONS_MINUTE,
                timezone=TZ
            ),
            id='daily_recommendations',
            name='Generate Daily Recommendations',
            replace_existing=True
        )

        # Job 2: Refresh in-memory cache
        scheduler.add_job(
            refresh_in_memory_cache,
            trigger=CronTrigger(
                hour=CRON_CACHE_REFRESH_HOUR,
                minute=CRON_CACHE_REFRESH_MINUTE,
                timezone=TZ
            ),
            id='daily_cache_refresh',
            name='Refresh In-Memory Cache',
            replace_existing=True
        )

        # Start the scheduler
        scheduler.start()

        logger.info(f"[SCHEDULER] ✓ Started with timezone: {SCHEDULER_TIMEZONE}")
        logger.info(
            f"[SCHEDULER] ✓ Job 1: Recommendations at "
            f"{CRON_RECOMMENDATIONS_HOUR:02d}:{CRON_RECOMMENDATIONS_MINUTE:02d} {SCHEDULER_TIMEZONE}"
        )
        logger.info(
            f"[SCHEDULER] ✓ Job 2: Cache refresh at "
            f"{CRON_CACHE_REFRESH_HOUR:02d}:{CRON_CACHE_REFRESH_MINUTE:02d} {SCHEDULER_TIMEZONE}"
        )

        # Log next run times
        for job in scheduler.get_jobs():
            logger.info(f"[SCHEDULER] Next run for '{job.name}': {job.next_run_time}")

    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to start: {e}")
        scheduler = None
        raise


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("[SCHEDULER] Stopped")


def get_scheduler_status():
    """Get current scheduler status"""
    if scheduler is None:
        return {
            'running': False,
            'message': 'Scheduler not started'
        }

    jobs = scheduler.get_jobs()
    if not jobs:
        return {
            'running': True,
            'jobs': [],
            'message': 'No scheduled jobs'
        }

    job_info = []
    for job in jobs:
        job_info.append({
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time),
            'trigger': str(job.trigger)
        })

    return {
        'running': True,
        'timezone': SCHEDULER_TIMEZONE,
        'jobs': job_info,
        'message': f'{len(jobs)} job(s) scheduled'
    }
