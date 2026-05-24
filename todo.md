# JobWatch Web Migration TODO

## Phase 1: Database Schema
- [x] Create jobs table (title, company, location, url, status, found_at, etc.)
- [x] Create company_suggestions table (company, ats_type, careers_url, verified, etc.)
- [x] Create job_queue table (pending job approvals)
- [x] Create user_profile table (address, username, password hint, etc.)
- [x] Create web_saves table (manually saved jobs from extension)
- [x] Create scan_log table (track scraper runs)

## Phase 2: Backend API (tRPC Procedures)
- [x] Jobs router (list, filter, update status, mark seen)
- [x] Companies router (list, approve, reject, discover new)
- [x] Profile router (get, update personal info)
- [x] Cover letter router (generate from job description)
- [x] Scraper router (trigger scan, get status)
- [x] Web saves router (save, list, update status)
- [x] Database helper functions (db.ts with all CRUD operations)

## Phase 3: Frontend Pages
- [x] Dashboard (job list with filters, stats)
- [x] Profile page (edit personal info, address, login helper)
- [x] Companies page (manage tracked companies)
- [ ] Saved jobs page (manually saved jobs)
- [ ] Settings page (scraper config, preferences)

## Phase 4: Sidebar Component
- [ ] Autofill sidebar (personal info, login helper, cover letter)
- [ ] Resume toggle (A/B versions)
- [ ] Experience section with copy buttons
- [ ] Cover letter generator UI

## Phase 4b: Daily Scraper & Job Comparison
- [x] Implement daily scraper with job comparison logic
- [x] Add job expiration tracking (mark jobs as expired if URL no longer exists)
- [x] Implement job deduplication and update logic
- [x] Add notification triggers for new relevant jobs

## Phase 4c: Email & In-App Notifications
- [x] Set up email notifications (to callmekhala@gmail.com)
- [x] Implement in-app notification system
- [ ] Create notification preferences/settings
- [ ] Test email delivery

## Phase 5: Scrapers & Scheduled Tasks
- [ ] Migrate Workday scraper logic
- [ ] Integrate Manus researcher with job filtering (only suggest companies with relevant jobs)
- [ ] Set up Heartbeat for 2-day discovery schedule
- [ ] Set up daily job scraping schedule

## Phase 6: Chrome Extension Sidebar
- [ ] Build extension sidebar component
- [ ] Implement API calls to hosted website
- [ ] Add personal info copy/paste functionality
- [ ] Integrate cover letter generator
- [ ] Add manual job save feature

## Phase 7: Deployment & Testing
- [ ] Configure environment variables
- [ ] Test authentication flow
- [ ] Test scraper execution
- [ ] Deploy to production
