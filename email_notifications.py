"""
Email Notification System
Sends email alerts when new high-scoring jobs are found.
Integrates with Flask app to notify user of matching opportunities.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from database import log_notification

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '')
RECIPIENT_EMAIL = os.environ.get('NOTIFICATION_EMAIL', 'callmekhala@gmail.com')

# Email settings
USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
USE_SSL = os.environ.get('SMTP_USE_SSL', 'false').lower() == 'true'

def send_email(subject: str, body_html: str, body_text: str = None) -> bool:
    """
    Send an email notification.
    
    Args:
        subject: Email subject line
        body_html: HTML email body
        body_text: Plain text fallback (auto-generated if not provided)
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("Email not configured (SENDER_EMAIL or SENDER_PASSWORD missing)")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        
        # Attach plain text version
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        else:
            # Simple text extraction from HTML
            text = body_html.replace('<br>', '\n').replace('<br/>', '\n')
            text = text.replace('<p>', '').replace('</p>', '\n')
            msg.attach(MIMEText(text, 'plain'))
        
        # Attach HTML version
        msg.attach(MIMEText(body_html, 'html'))
        
        # Connect and send
        if USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        
        if USE_TLS and not USE_SSL:
            server.starttls()
        
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent to {RECIPIENT_EMAIL}: {subject}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed - check SENDER_EMAIL and SENDER_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def send_new_job_alert(job_data: dict) -> bool:
    """
    Send an email alert for a new matching job.
    
    Args:
        job_data: Dictionary with keys: title, company, url, score, score_reasoning, location
    
    Returns:
        True if sent successfully
    """
    title = job_data.get('title', 'Unknown')
    company = job_data.get('company', 'Unknown')
    url = job_data.get('url', '#')
    score = job_data.get('score', 0)
    location = job_data.get('location', 'Remote')
    reasoning = job_data.get('score_reasoning', '')
    
    # Build HTML email
    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background: #ecf0f1; padding: 20px; border-radius: 0 0 5px 5px; }}
                .job-title {{ font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0; }}
                .company {{ font-size: 18px; color: #34495e; margin: 5px 0; }}
                .score {{ display: inline-block; background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .details {{ margin: 15px 0; }}
                .detail-row {{ margin: 8px 0; }}
                .label {{ font-weight: bold; color: #2c3e50; }}
                .button {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; margin-top: 15px; }}
                .reasoning {{ background: #fff; padding: 10px; border-left: 4px solid #3498db; margin-top: 15px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎯 New Job Match Found!</h2>
                </div>
                <div class="content">
                    <div class="job-title">{title}</div>
                    <div class="company">{company}</div>
                    <div style="margin-top: 10px;">
                        <span class="score">Match Score: {score}%</span>
                    </div>
                    
                    <div class="details">
                        <div class="detail-row">
                            <span class="label">📍 Location:</span> {location}
                        </div>
                        <div class="detail-row">
                            <span class="label">🔗 Job URL:</span><br>
                            <a href="{url}" class="button">View Job Posting</a>
                        </div>
                    </div>
                    
                    {f'<div class="reasoning"><strong>Why this match:</strong><br>{reasoning}</div>' if reasoning else ''}
                    
                    <p style="margin-top: 20px; font-size: 12px; color: #7f8c8d;">
                        This is an automated notification from JobWatch. 
                        Check your dashboard for more details and to manage your applications.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    subject = f"🎯 JobWatch: {company} - {title}"
    
    success = send_email(subject, html_body)
    
    if success:
        log_notification(
            job_id=job_data.get('id'),
            job_title=title,
            company=company,
            score=score,
            recipient=RECIPIENT_EMAIL
        )
    
    return success

def send_daily_digest(jobs: list) -> bool:
    """
    Send a daily digest email with all new matching jobs.
    
    Args:
        jobs: List of job dictionaries
    
    Returns:
        True if sent successfully
    """
    if not jobs:
        logger.info("No jobs to send in daily digest")
        return False
    
    # Build job list HTML
    jobs_html = ""
    for job in jobs:
        jobs_html += f"""
        <div style="border-bottom: 1px solid #bdc3c7; padding: 15px 0;">
            <div class="job-title" style="font-size: 18px;">{job.get('title', 'Unknown')}</div>
            <div class="company">{job.get('company', 'Unknown')}</div>
            <div style="margin-top: 8px;">
                <span class="score">{job.get('score', 0)}%</span>
                <span style="margin-left: 10px; color: #7f8c8d;">{job.get('location', 'Remote')}</span>
            </div>
            <a href="{job.get('url', '#')}" style="color: #3498db; text-decoration: none;">View Job →</a>
        </div>
        """
    
    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background: #ecf0f1; padding: 20px; border-radius: 0 0 5px 5px; }}
                .job-title {{ font-weight: bold; color: #2c3e50; }}
                .company {{ color: #34495e; font-size: 14px; }}
                .score {{ display: inline-block; background: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; }}
                .button {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 JobWatch Daily Digest</h2>
                    <p>You have {len(jobs)} new job matches today</p>
                </div>
                <div class="content">
                    {jobs_html}
                    
                    <div style="margin-top: 20px; text-align: center;">
                        <a href="http://localhost:5050" class="button">View All Jobs in Dashboard</a>
                    </div>
                    
                    <p style="margin-top: 20px; font-size: 12px; color: #7f8c8d;">
                        This is an automated notification from JobWatch.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    subject = f"📊 JobWatch Daily Digest - {len(jobs)} new matches"
    return send_email(subject, html_body)

def send_scan_report(scan_results: dict) -> bool:
    """
    Send a report after a scraper run.
    
    Args:
        scan_results: Dictionary with keys: companies_scanned, new_jobs, errors
    
    Returns:
        True if sent successfully
    """
    companies = scan_results.get('companies_scanned', 0)
    new_jobs = scan_results.get('new_jobs', 0)
    errors = scan_results.get('errors', [])
    
    error_html = ""
    if errors:
        error_html = "<div style='background: #ffe6e6; padding: 10px; border-radius: 3px; margin-top: 10px;'>"
        error_html += "<strong>⚠️ Errors encountered:</strong><ul>"
        for error in errors:
            error_html += f"<li>{error}</li>"
        error_html += "</ul></div>"
    
    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background: #ecf0f1; padding: 20px; border-radius: 0 0 5px 5px; }}
                .stat {{ display: inline-block; background: white; padding: 15px; margin: 10px 5px; border-radius: 3px; text-align: center; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                .stat-label {{ color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📋 JobWatch Scan Report</h2>
                    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="content">
                    <div>
                        <div class="stat">
                            <div class="stat-number">{companies}</div>
                            <div class="stat-label">Companies Scanned</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">{new_jobs}</div>
                            <div class="stat-label">New Jobs Found</div>
                        </div>
                    </div>
                    
                    {error_html}
                    
                    <p style="margin-top: 20px; font-size: 12px; color: #7f8c8d;">
                        This is an automated report from JobWatch scheduler.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    subject = f"📋 JobWatch Scan Report - {new_jobs} new jobs"
    return send_email(subject, html_body)

if __name__ == '__main__':
    # Test email sending
    logging.basicConfig(level=logging.INFO)
    
    # Check configuration
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️  Email not configured. Set SENDER_EMAIL and SENDER_PASSWORD in .env")
    else:
        print(f"✓ Email configured: {SENDER_EMAIL} → {RECIPIENT_EMAIL}")
        
        # Test sending
        test_job = {
            'title': 'Security Analyst',
            'company': 'Test Company',
            'url': 'https://example.com/jobs/123',
            'score': 85,
            'location': 'Cleveland, OH',
            'score_reasoning': 'Strong match for security analyst role with SIEM experience'
        }
        
        print("Sending test email...")
        if send_new_job_alert(test_job):
            print("✓ Test email sent successfully")
        else:
            print("✗ Failed to send test email")
