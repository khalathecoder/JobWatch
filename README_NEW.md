# JobWatch Pro - Intelligent Job Tracking & Application System

JobWatch is a sophisticated job search automation tool that combines web scraping, AI-powered job matching, and email notifications to help you find and track your ideal job opportunities. It integrates with Manus research for company discovery and Claude AI for intelligent job scoring.

## 🎯 Features

**🔍 Intelligent Job Discovery**
- Automatically scrapes job postings from approved companies
- Supports Workday, Greenhouse, Lever, and HTML-based career pages
- Discovers new companies via Manus research API
- Tracks job postings across multiple platforms

**🤖 AI-Powered Job Matching**
- Claude AI scores jobs based on your profile and preferences
- Identifies green flags (positive indicators) and red flags (concerns)
- Customizable scoring thresholds for notifications
- Learns from your preferences over time

**📧 Smart Notifications**
- Email alerts for high-matching job opportunities
- Daily digest emails with all new matches
- Scan reports after each scraper run
- Configurable notification frequency

**✅ Job Expiration Tracking**
- Automatically validates job URLs to detect expired postings
- Marks closed jobs as expired
- Maintains clean database of active opportunities
- Cleans up old expired jobs automatically

**💼 Application Management**
- Track job status (new, saved, applied, etc.)
- Save jobs from the web via Chrome extension
- Generate personalized cover letters with Claude
- Manage multiple resume versions

**📊 Dashboard & Analytics**
- Visual job statistics and trends
- Company performance tracking
- Preference history and learning
- Scan execution logs

**🔌 Chrome Extension**
- Save jobs directly from career pages
- Autofill application forms
- Quick access to your profile
- Badge showing unsaved jobs

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip or conda
- API keys for:
  - [Anthropic Claude](https://console.anthropic.com) (job scoring)
  - [Manus](https://manus.im) (company discovery)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/jobwatch.git
   cd JobWatch
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python -c "from database import init_db; init_db()"
   ```

6. **Run the app**
   ```bash
   # Terminal 1: Flask app
   python app.py
   
   # Terminal 2: Scheduler (in another terminal)
   python scheduler.py
   ```

7. **Access dashboard**
   - Open http://localhost:5050
   - Login with credentials from .env
   - Start adding companies to watch

## ⚙️ Configuration

### Environment Variables

**Flask Settings**
```
SECRET_KEY=your-random-secret-key
DASHBOARD_USERNAME=khala
DASHBOARD_PASSWORD=your-secure-password
EXTENSION_TOKEN=jobwatch-local
```

**Email Notifications**
```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
NOTIFICATION_EMAIL=your-email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**API Keys**
```
ANTHROPIC_API_KEY=your-claude-api-key
MANUS_API_KEY=your-manus-api-key
```

**Scheduler Settings**
```
SCAN_INTERVAL_DAYS=1
SUGGESTION_INTERVAL_DAYS=2
GRACE_PERIOD_DAYS=14
SCORE_THRESHOLD=70
```

### Email Setup

**Gmail:**
1. Enable 2-factor authentication
2. Generate app-specific password at https://myaccount.google.com/apppasswords
3. Use the generated password in SENDER_PASSWORD

**Other Providers:**
- Outlook: `smtp.office365.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- SendGrid: `smtp.sendgrid.net:587`

## 📖 Usage

### Dashboard

The main dashboard shows job statistics, active jobs with filters, and quick actions.

**Filters:** Status (All/New/Saved/Applied), Company, Age (Fire/Fresh/All/Archived), Keywords

### Company Management

1. Approve companies to add to your watchlist
2. View performance metrics for each company
3. Auto-rejection for companies with no jobs after grace period
4. Restore auto-rejected companies

### Job Queue

Review pending jobs before they're added to your main list. Jobs are scored and can be approved or rejected.

### Profile Management

Set up your profile for better job matching including personal info, professional summary, experience, skills, and certifications.

### Cover Letter Generation

Generate personalized cover letters using Claude AI with your profile and job description.

## 🔄 Scheduler

The scheduler runs automatically in the background performing:
- Job URL validation and expiration checking
- Company scraping for new postings
- Job scoring with Claude AI
- Email notifications for high-scoring jobs
- Company suggestions via Manus research
- Grace period checks for stale companies

## 🔌 API Endpoints

**Public:**
- `GET /api/ping` - Health check
- `POST /api/save-job` - Save job from extension
- `GET /api/badge-count` - Get unsaved jobs count

**Protected (requires login):**
- `GET /api/profile` - Get user profile
- `POST /api/cover-letter` - Generate cover letter
- `GET /api/web-saves` - Get saved web jobs
- `POST /api/web-saves/<id>` - Update save status
- `POST /api/trigger-scan` - Manually trigger scan
- `POST /api/trigger-score` - Manually trigger scoring
- `POST /api/trigger-suggestions` - Manually trigger suggestions

## 🐳 Deployment

For 24/7 operation, deploy to the cloud using Docker:

```bash
docker build -t jobwatch:latest .
docker-compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on:
- Railway (recommended)
- Render
- Heroku
- VPS (AWS, DigitalOcean, Linode)

## 🐛 Troubleshooting

**Jobs not being scraped:**
- Verify companies are approved in dashboard
- Check Manus API key is valid
- Review scraper logs: `tail -f logs/scheduler.log`

**Email notifications not sending:**
- Verify email credentials in .env
- For Gmail, use app-specific password (not regular password)
- Check SMTP server and port are correct
- Review email logs: `SELECT * FROM notification_log ORDER BY sent_at DESC`

**Scheduler not running:**
- Verify scheduler process is running: `ps aux | grep scheduler`
- Check scheduler logs for errors
- Ensure APScheduler is installed: `pip install APScheduler`

**App won't start:**
- Check all environment variables are set
- Verify database file exists and is writable
- Check logs for specific error messages
- Ensure all dependencies installed: `pip install -r requirements.txt`

## 📊 Architecture

The system consists of:
- **Flask Web App** - Dashboard and API
- **SQLite Database** - Job and company data
- **Background Scheduler** - Automated tasks
- **Claude API** - Job scoring
- **Manus API** - Company discovery

## 📝 License

This project is provided as-is for personal use.

## 💬 Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
2. Review logs: `tail -f logs/scheduler.log`
3. Check database: `sqlite3 jobwatch.db`
4. Review code comments for implementation details

---

**Happy job hunting! 🚀**
