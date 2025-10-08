"""
Automatic Task Scheduler
Runs daily recommendation generation at 3 AM automatically
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
import requests
import os

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def generate_daily_recommendations():
    """
    Task to generate recommendations for today
    Runs at 3 AM daily
    Generates for ALL routes automatically
    """
    try:
        # Get today's date (the day the cron is running)
        today = datetime.now().strftime('%Y-%m-%d')

        # Get API URL from environment or use localhost
        api_url = os.getenv('API_URL', 'http://localhost:8000')

        logger.info(f"[CRON] Starting daily recommendation generation for {today} (ALL routes)")

        try:
            # Call the pre-generate endpoint (generates ALL routes)
            url = f"{api_url}/api/v1/recommended-order/pre-generate-daily"
            params = {
                'date': today
            }

            response = requests.post(url, params=params, timeout=300)  # 5 min timeout

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"[CRON] ✓ {result.get('message')}")
                    routes_count = result.get('routes_count', 0)
                    records_saved = result.get('records_saved', 0)
                    logger.info(f"[CRON] ✓ Generated {records_saved} records across {routes_count} routes")
                else:
                    logger.warning(f"[CRON] ✗ {result.get('message')}")
            else:
                logger.error(f"[CRON] ✗ HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"[CRON] ✗ {str(e)}")

        logger.info(f"[CRON] Completed daily generation for {today}")

    except Exception as e:
        logger.error(f"[CRON] Failed to generate daily recommendations: {str(e)}")


def start_scheduler():
    """
    Start the background scheduler
    Runs at 3 AM daily (local server time)
    """
    global scheduler

    if scheduler is not None:
        logger.warning("[SCHEDULER] Scheduler already running")
        return

    try:
        # Create background scheduler
        scheduler = BackgroundScheduler(timezone='UTC')

        # Get cron schedule from environment or use default (3 AM)
        cron_hour = int(os.getenv('CRON_HOUR', '3'))
        cron_minute = int(os.getenv('CRON_MINUTE', '0'))

        # Add job to run at 3 AM daily
        scheduler.add_job(
            generate_daily_recommendations,
            trigger=CronTrigger(hour=cron_hour, minute=cron_minute),
            id='daily_recommendations',
            name='Generate Daily Recommendations',
            replace_existing=True
        )

        # Start the scheduler
        scheduler.start()

        logger.info(f"[SCHEDULER] ✓ Started - Will run daily at {cron_hour:02d}:{cron_minute:02d}")
        logger.info(f"[SCHEDULER] Next run: {scheduler.get_job('daily_recommendations').next_run_time}")

    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to start: {str(e)}")
        scheduler = None


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
        'jobs': job_info,
        'message': f'{len(jobs)} job(s) scheduled'
    }
