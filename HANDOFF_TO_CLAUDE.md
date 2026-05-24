# JobWatch Handoff to Claude

## Current Status

JobWatch is a Flask-based job tracking application with the following components:

### ✅ Completed
- Chrome extension for automatic job application detection (Manifest v3)
- Database schema with jobs, companies, profiles, notifications tables
- Email notification system
- Job expiration tracking
- Claude AI integration for job scoring
- Manus API research integration
- Comprehensive documentation (README, QUICKSTART, DEPLOYMENT, EXTENSION_SETUP)

### ⚠️ Current Issues
- Local Windows setup has SQLite schema conflicts
- Multiple database modules (database.py, profile_db.py, db_schema.py) with inconsistent schemas
- Flask app has import/routing issues when run locally
- Database initialization script exists but has edge cases

### 🎯 What Needs to Happen

**Priority 1: Fix Local Development**
1. Create a single, unified database module that all code uses
2. Ensure Flask app runs cleanly on Windows with `python app_clean.py`
3. Dashboard should load at `http://localhost:5000` without errors
4. Database should initialize cleanly with `python init_db_complete.py`

**Priority 2: Make Layout More Intuitive**
- Current dashboard has sidebar + main content
- User feedback: layout feels unintuitive
- Needs redesign for better UX (specifics TBD with user)

**Priority 3: Get App Running 24/7**
- Scheduler needs to run background jobs (scraping, scoring, notifications)
- Eventually deploy to cloud (Railway, Render, or similar)

## Key Files

### Database
- `db_schema.py` - **USE THIS** - Unified database module with all operations
- `init_db_complete.py` - Database initialization script
- `jobwatch.db` - SQLite database (can be deleted and recreated)

### Flask App
- `app_clean.py` - **USE THIS** - Clean Flask app (minimal dependencies)
- `app.py` - Old app (has issues, don't use)
- `requirements.txt` - Python dependencies

### Templates
- `templates/dashboard_new.html` - Modern dashboard (bright, energetic, playful design)
- `templates/` - Other template files

### Supporting Modules
- `scraper.py` - Job scraping logic
- `scheduler.py` - Background task scheduler
- `email_notifications.py` - Email sending
- `suggestions.py` - Claude-powered company suggestions
- `extension/` - Chrome extension files

## How to Use This Handoff

1. **Extract this zip file**
2. **Read the key files:**
   - `db_schema.py` - Understand the database structure
   - `app_clean.py` - Understand the Flask app
   - `templates/dashboard_new.html` - See the UI design
3. **Ask the user:**
   - What specifically feels unintuitive about the layout?
   - What's their priority: get it working locally first, or design/UX?
4. **Fix issues in order:**
   - Database/Flask app issues first
   - Then UX/layout improvements
   - Then 24/7 deployment

## Quick Start (What Should Work)

```bash
# Delete old database
rm jobwatch.db

# Initialize fresh database
python init_db_complete.py

# Run Flask app
python app_clean.py

# Visit http://localhost:5000
```

## Notes for Claude

- User is frustrated with back-and-forth troubleshooting
- They want a working solution, not more debugging
- Focus on **one thing at a time** and verify it works before moving on
- The architecture is sound; just needs cleanup and UX polish
- User has GitHub repo at: https://github.com/khalathecoder/JobWatch

## Questions for User

When you take over, ask:
1. What specifically feels unintuitive about the dashboard layout?
2. Should the app prioritize: (a) getting it working locally, (b) better UX, (c) 24/7 deployment?
3. Any specific features they want to add or change?

---

Good luck! This project has solid bones—just needs some finishing touches. 🚀
