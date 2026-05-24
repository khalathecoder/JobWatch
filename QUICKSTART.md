# JobWatch Quick Start Guide

Get JobWatch running in 5 minutes with these simple steps.

## 1. Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

## 2. Configure Environment (1 minute)

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required: Login credentials
SECRET_KEY=your-random-secret-key-here
DASHBOARD_USERNAME=khala
DASHBOARD_PASSWORD=your-password

# Optional but recommended: Email notifications
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
NOTIFICATION_EMAIL=your-email@gmail.com

# Required: API keys for job scoring and company discovery
ANTHROPIC_API_KEY=sk-...
MANUS_API_KEY=...
```

## 3. Initialize Database (1 minute)

```bash
python -c "from database import init_db, init_queue_tables; from profile_db import init_profile_tables; from settings_db import init_settings; init_db(); init_queue_tables(); init_profile_tables(); init_settings(); print('✓ Database initialized')"
```

## 4. Run the App (2 minutes)

**Terminal 1: Start Flask app**
```bash
python app.py
```

You should see:
```
  JobWatch → http://localhost:5050
```

**Terminal 2: Start scheduler (in another terminal)**
```bash
python scheduler.py
```

You should see:
```
JobWatch Scheduler started
  Scan interval:    every 1 day(s)
  Suggest interval: every 2 day(s)
```

## 5. Access Dashboard

Open your browser to: **http://localhost:5050**

Login with your credentials from `.env`

## What to Do Next

1. **Add Your Profile**
   - Click "Profile" in the sidebar
   - Fill in your personal info, experience, skills
   - This helps the AI score jobs better

2. **Approve Companies**
   - Click "Companies" in the sidebar
   - Review suggested companies
   - Click "Approve" on companies you want to watch

3. **Wait for First Scan**
   - Scheduler runs immediately on startup
   - Check "Dashboard" to see new jobs
   - Check your email for notifications

4. **Review & Approve Jobs**
   - Click "Queue" to see pending jobs
   - Review AI scoring and reasoning
   - Approve jobs you're interested in
   - They'll move to your main dashboard

## Email Setup (Optional but Recommended)

### Gmail

1. Enable 2-factor authentication: https://myaccount.google.com/security
2. Generate app-specific password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password
4. Add to `.env`:
   ```
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx
   ```

### Other Email Providers

**Outlook:**
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**Yahoo:**
```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**SendGrid:**
```
SENDER_EMAIL=apikey
SENDER_PASSWORD=SG.your-api-key
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
```

## Troubleshooting

**App won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep -E "flask|requests|anthropic"

# Check for syntax errors
python -m py_compile app.py
```

**Scheduler won't start:**
```bash
# Check APScheduler is installed
pip list | grep APScheduler

# Check .env file exists
ls -la .env

# Run with verbose logging
python scheduler.py -v
```

**Database error:**
```bash
# Delete old database and reinitialize
rm jobwatch.db
python -c "from database import init_db; init_db(); print('✓ Database reset')"
```

**Email not sending:**
```bash
# Check credentials in .env
cat .env | grep SENDER

# For Gmail, verify app-specific password (not regular password)
# Check SMTP settings match your provider
```

## Manual Triggers

Once the app is running, you can manually trigger operations:

**Trigger a scan:**
```bash
curl -X POST http://localhost:5050/api/trigger-scan \
  -H "Content-Type: application/json"
```

**Trigger job scoring:**
```bash
curl -X POST http://localhost:5050/api/trigger-score \
  -H "Content-Type: application/json"
```

**Trigger company suggestions:**
```bash
curl -X POST http://localhost:5050/api/trigger-suggestions \
  -H "Content-Type: application/json"
```

## Next Steps

1. **Test with Docker** (for deployment):
   ```bash
   docker-compose up
   ```

2. **Deploy to Cloud** (for 24/7 operation):
   - See [DEPLOYMENT.md](DEPLOYMENT.md)
   - Railway recommended (easiest setup)

3. **Customize Settings**:
   - Go to "Settings" in dashboard
   - Adjust score threshold for notifications
   - Configure archive settings
   - Set keyword preferences

4. **Install Chrome Extension** (optional):
   - See extension folder for setup
   - Save jobs directly from career pages
   - Autofill application forms

## Key Files

- `app.py` - Flask web application
- `scheduler.py` - Background job scheduler
- `database.py` - Database operations
- `job_expiration.py` - URL validation
- `email_notifications.py` - Email alerts
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `DEPLOYMENT.md` - Cloud deployment guide

## Support

- Check logs: `tail -f logs/scheduler.log`
- Check database: `sqlite3 jobwatch.db`
- Review code comments for details
- See README.md for full documentation

---

**You're all set! Happy job hunting! 🚀**
