"""
JobWatch Scheduler — runs independently of the Flask app.
Starts with Windows, scans companies every 2 days, suggests new companies on interval.
"""
import sys, os, time, logging
from datetime import datetime

# Ensure we can import from jobwatch directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_PATH = os.path.join(os.path.dirname(__file__), 'scheduler.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger('jobwatch.scheduler')

def run_scan():
    try:
        log.info('── Scheduled scan starting ──')
        from database import init_db, init_queue_tables
        from settings_db import init_settings, get_grace_days
        from profile_db import init_profile_tables
        init_db(); init_queue_tables(); init_profile_tables(); init_settings()

        from scraper import run_scrape
        results = run_scrape()
        total_new = sum(r.get('new', 0) for r in results)
        log.info(f'Scan complete — {len(results)} companies, {total_new} new jobs queued')

        from suggestions import score_pending_jobs
        log.info('Scoring pending jobs...')
        score_pending_jobs()
        log.info('Scoring complete')

    except Exception as e:
        log.error(f'Scan error: {e}', exc_info=True)

def run_suggestions():
    try:
        log.info('── Scheduled company suggestions ──')
        from suggestions import run_company_suggestions
        added = run_company_suggestions()
        log.info(f'Company suggestions complete — {added} new suggestions added')
    except Exception as e:
        log.error(f'Suggestion error: {e}', exc_info=True)

def main():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from dotenv import load_dotenv

    # Load .env from same directory as this script
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)

    # Init DB on startup
    try:
        from database import init_db, init_queue_tables
        from settings_db import init_settings, get
        from profile_db import init_profile_tables
        init_db(); init_queue_tables(); init_profile_tables(); init_settings()
        scan_interval_days     = 2
        suggest_interval_days  = int(get('suggestion_interval') or 2)
    except Exception as e:
        log.error(f'Init error: {e}', exc_info=True)
        sys.exit(1)

    scheduler = BlockingScheduler(timezone='America/New_York')

    # Scan every 2 days
    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(days=scan_interval_days),
        id='company_scan',
        name='Scan all watchlist companies',
        replace_existing=True
    )

    # Suggest new companies per configured interval
    scheduler.add_job(
        run_suggestions,
        trigger=IntervalTrigger(days=suggest_interval_days),
        id='company_suggestions',
        name='Suggest new companies via Claude',
        replace_existing=True
    )

    log.info('='*50)
    log.info('JobWatch Scheduler started')
    log.info(f'  Scan interval:    every {scan_interval_days} days')
    log.info(f'  Suggest interval: every {suggest_interval_days} days')
    log.info(f'  Log file:         {LOG_PATH}')
    log.info('='*50)

    # Run once immediately on startup
    log.info('Running initial scan on startup...')
    run_scan()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info('Scheduler stopped.')
        scheduler.shutdown()

if __name__ == '__main__':
    main()
