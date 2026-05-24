# JobWatch Flask App Enhancement TODO

## Phase 1: Fix Database & Core Issues ✅
- [x] Fix database schema inconsistencies (merge init_db and init_queue_tables)
- [x] Create web_saves table in database initialization
- [x] Add missing columns (passion_statement, approved_at, etc.)
- [x] Fix app.py route registration (move routes before app.run())
- [x] Add missing imports (init_approved_companies, add_approved_company, update_last_scanned)
- [x] Fix profile_db.py schema to include passion_statement column
- [x] Test all database operations work correctly

## Phase 2: Job Expiration & Validation ✅
- [x] Create job_expiration.py module with URL validation
- [x] Implement check_url_valid() to detect expired jobs
- [x] Add check_all_jobs_expiration() for batch processing
- [x] Implement automatic marking of expired jobs as 'closed'
- [x] Add cleanup_old_expired_jobs() to maintain database performance
- [x] Integrate into scheduler for automatic checking

## Phase 3: Email Notifications ✅
- [x] Create email_notifications.py module
- [x] Implement send_email() with SMTP support (Gmail, Outlook, SendGrid)
- [x] Create send_new_job_alert() for individual job notifications
- [x] Create send_daily_digest() for batch notifications
- [x] Create send_scan_report() for scheduler reports
- [x] Add notification_log table to database
- [x] Integrate email alerts into scheduler

## Phase 4: Scheduler Integration ✅
- [x] Update scheduler.py to call job expiration checker
- [x] Add email notification sending to scan cycle
- [x] Implement run_grace_period_check() for auto-rejecting stale companies
- [x] Add configurable intervals via environment variables
- [x] Improve logging with detailed scan reports

## Phase 5: Production Deployment ✅
- [x] Create Dockerfile for containerization
- [x] Create docker-compose.yml for local testing
- [x] Add gunicorn and psycopg2 to requirements.txt
- [x] Create comprehensive DEPLOYMENT.md guide
- [x] Document Railway, Render, Heroku, and VPS deployment options
- [x] Add health check endpoint (/api/ping)
- [x] Document email configuration for Gmail, Outlook, SendGrid

## Phase 6: Testing & Documentation
- [ ] Test Docker build locally: `docker-compose build`
- [ ] Test app startup: `docker-compose up`
- [ ] Verify all routes are accessible
- [ ] Test job expiration with sample URLs
- [ ] Test email notifications with test credentials
- [ ] Test scheduler runs on schedule
- [ ] Create quick start guide for users
- [ ] Document all API endpoints

## Phase 7: Chrome Extension (Optional)
- [ ] Create manifest.json for Chrome extension
- [ ] Build extension popup UI
- [ ] Implement job capture functionality
- [ ] Add autofill for application forms
- [ ] Test with real job sites
- [ ] Package as .crx file

## Known Issues & Improvements
- [ ] Add PostgreSQL support for production (currently SQLite)
- [ ] Implement caching for company discovery
- [ ] Add rate limiting to prevent API abuse
- [ ] Create admin dashboard for monitoring
- [ ] Add backup/restore functionality
- [ ] Implement job deduplication logic
- [ ] Add user preferences for notification frequency

## Configuration Checklist
Before deployment, ensure:
- [ ] SECRET_KEY is set to a random value
- [ ] DASHBOARD_USERNAME and DASHBOARD_PASSWORD are strong
- [ ] SENDER_EMAIL and SENDER_PASSWORD are configured
- [ ] ANTHROPIC_API_KEY is valid
- [ ] MANUS_API_KEY is valid
- [ ] NOTIFICATION_EMAIL is correct
- [ ] SMTP settings match your email provider
- [ ] All environment variables are in .env file


## Phase 6: Chrome Extension - Automatic Application Detection ✅
- [x] Create Chrome extension manifest.json
- [x] Implement form submission detection (all job sites)
- [x] Add job URL extraction from current page
- [x] Implement API call to mark job as "applied"
- [x] Add confirmation notification in extension
- [x] Handle edge cases (multiple applications, same job)
- [x] Create extension installation guide (EXTENSION_SETUP.md)
- [x] Create backend API endpoints (extension_api.py)
- [x] Integrate extension API into Flask app (app.py)
