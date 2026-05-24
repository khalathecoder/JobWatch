"""
JobWatch Scheduler — runs independently of the Flask app.
Starts with Windows, scans companies every 2 days, suggests new companies on interval.
Includes job expiration checking and email notifications.
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
    """Run a complete scan cycle: check expiration, scrape, score, and notify."""
    try:
        log.info('── Scheduled scan starting ──')
        from database import init_db, init_queue_tables, get_pending_jobs, get_settings
        from settings_db import init_settings
        from profile_db import init_profile_tables
        init_db()
        init_queue_tables()
        init_profile_tables()
        init_settings()

        # Check for expired jobs
        log.info('Checking for expired jobs...')
        from job_expiration import check_all_jobs_expiration, cleanup_old_expired_jobs
        exp_stats = check_all_jobs_expiration()
        log.info(f'Expiration check: {exp_stats["expired_count"]} expired, {exp_stats["valid_count"]} valid')
        cleanup_old_expired_jobs(days=30)

        # Run scraper
        from scraper import run_scrape
        results = run_scrape(discover=True)
        total_new = sum(r.get('new', 0) for r in results)
        log.info(f'Scan complete — {len(results)} companies, {total_new} new jobs queued')

        # Score pending jobs
        from suggestions import score_pending_jobs
        log.info('Scoring pending jobs...')
        score_pending_jobs()
        log.info('Scoring complete')

        # Send email notifications for high-scoring jobs
        log.info('Sending email notifications...')
        from email_notifications import send_new_job_alert, send_scan_report
        settings = get_settings()
        threshold = int(settings.get('score_threshold', 70))
        
        pending = get_pending_jobs(threshold)
        notified_count = 0
        for job in pending:
            try:
                send_new_job_alert({
                    'id': job['id'],
                    'title': job['title'],
                    'company': job['company'],
                    'url': job['url'],
                    'score': job['score'],
                    'location': job.get('location', 'Remote'),
                    'score_reasoning': job.get('score_reasoning', '')
                })
                notified_count += 1
            except Exception as e:
                log.warning(f'Failed to notify for job {job["id"]}: {e}')
        
        if notified_count > 0:
            log.info(f'Sent {notified_count} email notifications')
        
        # Send scan report
        send_scan_report({
            'companies_scanned': len(results),
            'new_jobs': total_new,
            'errors': exp_stats.get('errors', [])
        })

    except Exception as e:
        log.error(f'Scan error: {e}', exc_info=True)

def run_suggestions():
    """Run company suggestion pipeline to discover new companies."""
    try:
        log.info('── Scheduled company suggestions ──')
        from suggestions import run_company_suggestions
        added = run_company_suggestions()
        log.info(f'Company suggestions complete — {added} new suggestions added')
    except Exception as e:
        log.error(f'Suggestion error: {e}', exc_info=True)

def run_grace_period_check():
    """Check for companies in grace period with no jobs and auto-reject them."""
    try:
        log.info('── Checking grace period for companies ──')
        from database import check_and_auto_reject
        auto_rejected = check_and_auto_reject(grace_days=14)
        if auto_rejected:
            log.info(f'Auto-rejected {len(auto_rejected)} companies with no jobs after grace period')
            for co in auto_rejected:
                log.debug(f'  - {co["name"]} (suggested {co["suggested_at"]})')
    except Exception as e:
        log.error(f'Grace period check error: {e}', exc_info=True)

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
        init_db()
        init_queue_tables()
        init_profile_tables()
        init_settings()
        
        scan_interval_days = int(os.environ.get('SCAN_INTERVAL_DAYS', 1))
        suggest_interval_days = int(os.environ.get('SUGGESTION_INTERVAL_DAYS', 2))
        grace_check_interval_days = int(os.environ.get('GRACE_CHECK_INTERVAL_DAYS', 7))
    except Exception as e:
        log.error(f'Init error: {e}', exc_info=True)
        sys.exit(1)

    scheduler = BlockingScheduler(timezone='America/New_York')

    # Scan every N days (default 1)
    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(days=scan_interval_days),
        id='company_scan',
        name='Scan all watchlist companies',
        replace_existing=True
    )

    # Suggest new companies per configured interval (default 2 days)
    scheduler.add_job(
        run_suggestions,
        trigger=IntervalTrigger(days=suggest_interval_days),
        id='company_suggestions',
        name='Suggest new companies via Claude',
        replace_existing=True
    )

    # Check grace period every N days (default 7)
    scheduler.add_job(
        run_grace_period_check,
        trigger=IntervalTrigger(days=grace_check_interval_days),
        id='grace_period_check',
        name='Auto-reject companies with no jobs',
        replace_existing=True
    )

    log.info('='*60)
    log.info('JobWatch Scheduler started')
    log.info(f'  Scan interval:         every {scan_interval_days} day(s)')
    log.info(f'  Suggest interval:      every {suggest_interval_days} day(s)')
    log.info(f'  Grace period check:    every {grace_check_interval_days} day(s)')
    log.info(f'  Log file:              {LOG_PATH}')
    log.info('='*60)

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
