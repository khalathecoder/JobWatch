#!/usr/bin/env python3
"""
Complete database initialization script.
Run this to create/reset the database with all correct schemas.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

def init_complete_db():
    """Create all tables with correct schemas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop all existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    
    # Create all tables with complete schemas
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
    
    cursor.execute('''
        CREATE TABLE profile_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT UNIQUE NOT NULL,
            summary TEXT,
            passion_statement TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
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
    
    conn.commit()
    conn.close()
    print(f'✓ Database initialized at {DB_PATH}')

if __name__ == '__main__':
    init_complete_db()
