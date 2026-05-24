# JobWatch Deployment Guide

This guide covers deploying JobWatch to cloud platforms for 24/7 operation.

## Prerequisites

Before deploying, ensure you have:

1. **Environment Variables Configured** - All secrets in `.env`:
   - `SECRET_KEY` - Random secret for Flask sessions
   - `DASHBOARD_USERNAME` & `DASHBOARD_PASSWORD` - Login credentials
   - `SENDER_EMAIL` & `SENDER_PASSWORD` - Email credentials for notifications
   - `ANTHROPIC_API_KEY` - Claude API key for job scoring
   - `MANUS_API_KEY` - Manus API key for company discovery

2. **Docker Installed** (for local testing):
   ```bash
   docker --version
   docker-compose --version
   ```

## Local Testing with Docker

Test the deployment locally before pushing to cloud:

```bash
# Build the Docker image
docker-compose build

# Start both app and scheduler
docker-compose up

# In another terminal, test the app
curl http://localhost:5050/api/ping

# View logs
docker-compose logs -f app
docker-compose logs -f scheduler

# Stop services
docker-compose down
```

## Deployment Options

### Option 1: Railway (Recommended)

Railway provides free tier with SQLite support and automatic scheduling.

**Steps:**

1. Sign up at [railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository (or use CLI)
4. Add environment variables in Railway dashboard:
   - Go to Variables tab
   - Add all variables from `.env`
5. Deploy:
   ```bash
   npm install -g @railway/cli
   railway link
   railway up
   ```

**For Scheduler:**
- Railway supports background jobs via cron
- Create a separate service for `python scheduler.py`
- Or use Railway's built-in cron trigger

### Option 2: Render

Render provides free tier with background workers.

**Steps:**

1. Sign up at [render.com](https://render.com)
2. Create a new Web Service
3. Connect GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:5050 --workers 4 app:app`
5. Add environment variables in Render dashboard
6. Deploy

**For Scheduler:**
- Create a separate Background Worker service
- Start Command: `python scheduler.py`
- This runs continuously in background

### Option 3: Heroku (Legacy)

Heroku removed free tier but still supports paid deployments.

```bash
# Install Heroku CLI
brew install heroku

# Login
heroku login

# Create app
heroku create jobwatch-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret
heroku config:set SENDER_EMAIL=your-email@gmail.com
# ... set all other variables

# Deploy
git push heroku main

# View logs
heroku logs --tail

# Create scheduler dyno
heroku ps:scale scheduler=1
```

### Option 4: Docker Hub + Any VPS

Deploy using Docker to any VPS (AWS, DigitalOcean, Linode, etc.).

**Steps:**

1. Push Docker image to Docker Hub:
   ```bash
   docker build -t yourusername/jobwatch:latest .
   docker push yourusername/jobwatch:latest
   ```

2. On your VPS:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Create .env file with all secrets
   nano .env

   # Run with docker-compose
   docker-compose up -d
   ```

## Database Persistence

### SQLite (Default)

SQLite works for small deployments but has limitations:
- Single-file database (`jobwatch.db`)
- Not ideal for concurrent access
- Suitable for personal use

**Backup strategy:**
```bash
# Download database regularly
scp user@server:/app/jobwatch.db ./backup-$(date +%Y%m%d).db
```

### PostgreSQL (Recommended for Production)

For larger deployments, migrate to PostgreSQL:

1. Install PostgreSQL on your server or use managed service (AWS RDS, Heroku Postgres, etc.)
2. Update `database.py` to use PostgreSQL instead of SQLite:
   ```python
   import psycopg2
   # Replace sqlite3 with psycopg2
   ```
3. Run migrations to create tables in PostgreSQL

## Email Configuration

### Gmail

1. Enable 2-factor authentication on your Google account
2. Generate app-specific password:
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Windows Computer" (or your device)
   - Copy the generated password
3. Set environment variables:
   ```
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx  (16-character app password)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=true
   ```

### Other Email Providers

**Outlook/Office 365:**
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**SendGrid:**
```
SENDER_EMAIL=apikey
SENDER_PASSWORD=SG.your-sendgrid-api-key
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
```

## Monitoring & Logs

### View Application Logs

**Railway:**
```bash
railway logs
```

**Render:**
- View in dashboard under "Logs" tab

**Docker/VPS:**
```bash
docker-compose logs -f app
docker-compose logs -f scheduler
```

### Health Checks

The app includes a health check endpoint:
```bash
curl https://your-app.com/api/ping
# Response: {"status": "ok", "version": "1.0"}
```

### Monitor Scheduler

Check scheduler logs:
```bash
# Local
tail -f logs/scheduler.log

# Remote
ssh user@server
tail -f /app/logs/scheduler.log
```

## Troubleshooting

### App won't start

1. Check environment variables are set correctly
2. Verify database file exists and is writable
3. Check logs for specific error messages
4. Ensure all dependencies are installed: `pip install -r requirements.txt`

### Scheduler not running

1. Verify scheduler service is running:
   ```bash
   docker-compose ps
   ```
2. Check scheduler logs for errors
3. Ensure APScheduler is installed: `pip install APScheduler`

### Email notifications not sending

1. Verify email credentials in environment variables
2. Check SMTP server and port are correct
3. For Gmail, ensure app-specific password is used (not regular password)
4. Check email logs in database: `SELECT * FROM notification_log ORDER BY sent_at DESC`

### Jobs not being scraped

1. Check that companies are approved in dashboard
2. Verify Manus API key is valid
3. Check Anthropic API key is valid
4. Review scraper logs for specific errors

## Performance Optimization

### For High Job Volume

1. **Increase worker count** in Dockerfile:
   ```dockerfile
   CMD ["gunicorn", "--workers", "8", ...]
   ```

2. **Optimize database queries**:
   - Add indexes on frequently queried columns
   - Archive old jobs regularly

3. **Batch email notifications**:
   - Instead of sending individual emails, send daily digest
   - Modify scheduler to use `send_daily_digest()` instead of `send_new_job_alert()`

### Caching

Add Redis for caching (optional):
```bash
docker run -d -p 6379:6379 redis:latest
```

## Backup & Recovery

### Automated Backups

Set up daily backups:

```bash
# Create backup script (backup.sh)
#!/bin/bash
BACKUP_DIR="/backups/jobwatch"
mkdir -p $BACKUP_DIR
cp /app/jobwatch.db $BACKUP_DIR/jobwatch-$(date +%Y%m%d-%H%M%S).db

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete

# Schedule with cron
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Stop the app
docker-compose down

# Restore database
cp /backups/jobwatch/jobwatch-YYYYMMDD-HHMMSS.db ./jobwatch.db

# Restart
docker-compose up -d
```

## Security Considerations

1. **Use HTTPS** - Enable SSL/TLS on your domain
2. **Rotate secrets** - Change passwords and API keys regularly
3. **Limit access** - Use VPN or IP whitelisting for dashboard
4. **Keep dependencies updated** - Run `pip install --upgrade -r requirements.txt`
5. **Monitor logs** - Set up alerts for errors or suspicious activity

## Next Steps

After deployment:

1. Test the dashboard at `https://your-app.com`
2. Verify scheduler is running by checking logs
3. Wait for first scan cycle to complete
4. Check email for notifications
5. Monitor performance and adjust as needed

For questions or issues, check the logs first and review this guide.
