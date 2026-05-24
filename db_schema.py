"""
Unified database schema and helpers.
Single source of truth for all database operations.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

def get_conn():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all tables."""
    conn = get_conn()
    cursor = conn.cursor()
    
    # Drop all existing tables to start fresh
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    
    # Jobs table
    cursor.execute('''
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            posted_date TEXT,
            status TEXT DEFAULT 'new',
            score INTEGER DEFAULT 0,
            match_reason TEXT,
            source TEXT DEFAULT 'scraper',
            seen INTEGER DEFAULT 0,
            applied_date TEXT,
            found_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Approved companies
    cursor.execute('''
        CREATE TABLE approved_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sector TEXT,
            ats_type TEXT DEFAULT 'Unknown',
            workday_tenant TEXT,
            careers_url TEXT,
            hq TEXT,
            why_added TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Company suggestions
    cursor.execute('''
        CREATE TABLE company_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sector TEXT,
            ats_type TEXT DEFAULT 'Unknown',
            hq TEXT,
            careers_url TEXT,
            why_suggested TEXT,
            sample_roles TEXT DEFAULT '[]',
            has_live_roles INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            workday_tenant TEXT,
            status TEXT DEFAULT 'pending',
            approved_at TEXT,
            total_jobs_found INTEGER DEFAULT 0,
            last_job_found TEXT,
            scan_count INTEGER DEFAULT 0,
            last_scanned TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Web saves
    cursor.execute('''
        CREATE TABLE web_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'saved',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Profile summary
    cursor.execute('''
        CREATE TABLE profile_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT UNIQUE NOT NULL,
            summary TEXT DEFAULT '',
            passion_statement TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Profile info (key-value store)
    cursor.execute('''
        CREATE TABLE profile_info (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    ''')
    
    # Experience
    cursor.execute('''
        CREATE TABLE experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT DEFAULT 'both',
            job_title TEXT,
            company TEXT,
            start_date TEXT,
            end_date TEXT,
            responsibilities TEXT DEFAULT '[]',
            sort_order INTEGER DEFAULT 0
        )
    ''')
    
    # Education
    cursor.execute('''
        CREATE TABLE education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            degree TEXT,
            school TEXT,
            graduation_date TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')
    
    # Skills
    cursor.execute('''
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT DEFAULT 'both',
            category TEXT,
            items TEXT
        )
    ''')
    
    # Certifications
    cursor.execute('''
        CREATE TABLE certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    ''')
    
    # Notifications
    cursor.execute('''
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            email_sent INTEGER DEFAULT 0,
            sent_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    ''')
    
    # Settings
    cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f'✓ Database initialized at {DB_PATH}')

# ============================================================================
# JOB OPERATIONS
# ============================================================================

def add_job(company, title, url, description='', posted_date='', source='scraper'):
    """Add a new job."""
    conn = get_conn()
    try:
        conn.execute('''
            INSERT INTO jobs (company, title, url, description, posted_date, source, found_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (company, title, url, description, posted_date, source, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # URL already exists
    finally:
        conn.close()

def get_jobs(status_filter=None, keyword_filter=None, company_filter=None):
    """Get jobs with optional filters."""
    conn = get_conn()
    query = 'SELECT * FROM jobs WHERE 1=1'
    params = []
    
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    if keyword_filter:
        query += ' AND (title LIKE ? OR description LIKE ?)'
        params.extend([f'%{keyword_filter}%', f'%{keyword_filter}%'])
    if company_filter:
        query += ' AND company = ?'
        params.append(company_filter)
    
    query += ' ORDER BY created_at DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_job_status(job_id, status):
    """Update job status."""
    conn = get_conn()
    conn.execute('UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?',
                 (status, datetime.now().isoformat(), job_id))
    conn.commit()
    conn.close()

def update_job_score(job_id, score, match_reason=''):
    """Update job score and match reason."""
    conn = get_conn()
    conn.execute('UPDATE jobs SET score = ?, match_reason = ?, updated_at = ? WHERE id = ?',
                 (score, match_reason, datetime.now().isoformat(), job_id))
    conn.commit()
    conn.close()

def mark_job_applied(job_id, applied_date=None):
    """Mark job as applied."""
    conn = get_conn()
    if applied_date is None:
        applied_date = datetime.now().isoformat()
    conn.execute('UPDATE jobs SET status = ?, applied_date = ?, updated_at = ? WHERE id = ?',
                 ('applied', applied_date, datetime.now().isoformat(), job_id))
    conn.commit()
    conn.close()

# ============================================================================
# COMPANY OPERATIONS
# ============================================================================

def add_approved_company(name, sector='', ats_type='Unknown', workday_tenant='', 
                        careers_url='', hq='', why_added=''):
    """Add an approved company."""
    conn = get_conn()
    try:
        conn.execute('''
            INSERT INTO approved_companies (name, sector, ats_type, workday_tenant, careers_url, hq, why_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, sector, ats_type, workday_tenant, careers_url, hq, why_added))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_approved_companies():
    """Get all approved companies."""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM approved_companies ORDER BY name').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def suggest_company(name, sector='', ats_type='Unknown', hq='', careers_url='', 
                   why_suggested='', sample_roles='[]'):
    """Suggest a new company."""
    conn = get_conn()
    try:
        conn.execute('''
            INSERT INTO company_suggestions (name, sector, ats_type, hq, careers_url, why_suggested, sample_roles)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, sector, ats_type, hq, careers_url, why_suggested, sample_roles))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_company_suggestions(status='pending'):
    """Get company suggestions."""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM company_suggestions WHERE status = ? ORDER BY created_at DESC',
                       (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_company_suggestion(suggestion_id):
    """Approve a company suggestion and move it to approved companies."""
    conn = get_conn()
    suggestion = conn.execute('SELECT * FROM company_suggestions WHERE id = ?', 
                             (suggestion_id,)).fetchone()
    if suggestion:
        add_approved_company(
            suggestion['name'],
            suggestion['sector'],
            suggestion['ats_type'],
            suggestion['workday_tenant'],
            suggestion['careers_url'],
            suggestion['hq'],
            f"Suggested: {suggestion['why_suggested']}"
        )
        conn.execute('UPDATE company_suggestions SET status = ?, approved_at = ? WHERE id = ?',
                    ('approved', datetime.now().isoformat(), suggestion_id))
        conn.commit()
    conn.close()

# ============================================================================
# PROFILE OPERATIONS
# ============================================================================

def save_profile_info(data):
    """Save profile info (key-value pairs)."""
    conn = get_conn()
    for k, v in data.items():
        conn.execute('INSERT OR REPLACE INTO profile_info (key, value) VALUES (?, ?)', (k, v))
    conn.commit()
    conn.close()

def get_profile_info():
    """Get all profile info."""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM profile_info').fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def save_summary(version, summary_text):
    """Save profile summary."""
    conn = get_conn()
    conn.execute('''
        INSERT OR REPLACE INTO profile_summary (resume_version, summary, updated_at)
        VALUES (?, ?, ?)
    ''', (version, summary_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_passion_statement(passion_text):
    """Save passion statement."""
    conn = get_conn()
    conn.execute('''
        INSERT OR REPLACE INTO profile_summary (resume_version, passion_statement, updated_at)
        VALUES (?, ?, ?)
    ''', ('passion', passion_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_profile_summary():
    """Get profile summary."""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM profile_summary').fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r['resume_version']] = {
            'summary': r['summary'],
            'passion_statement': r['passion_statement']
        }
    return result

# ============================================================================
# NOTIFICATION OPERATIONS
# ============================================================================

def add_notification(job_id, email_sent=0):
    """Add a notification."""
    conn = get_conn()
    conn.execute('''
        INSERT INTO notifications (job_id, email_sent)
        VALUES (?, ?)
    ''', (job_id, email_sent))
    conn.commit()
    conn.close()

def mark_notification_sent(notification_id):
    """Mark notification as sent."""
    conn = get_conn()
    conn.execute('''
        UPDATE notifications SET email_sent = 1, sent_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), notification_id))
    conn.commit()
    conn.close()

def get_unsent_notifications():
    """Get unsent notifications."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT n.*, j.company, j.title, j.url FROM notifications n
        JOIN jobs j ON n.job_id = j.id
        WHERE n.email_sent = 0
        ORDER BY n.created_at DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == '__main__':
    init_db()
