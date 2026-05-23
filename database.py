import sqlite3, json, os
DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS jobs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            company   TEXT NOT NULL,
            title     TEXT NOT NULL,
            location  TEXT,
            url       TEXT NOT NULL UNIQUE,
            posted_on TEXT,
            keywords  TEXT,
            status    TEXT DEFAULT 'new',
            seen      INTEGER DEFAULT 0,
            found_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS job_queue (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            company        TEXT NOT NULL,
            title          TEXT NOT NULL,
            location       TEXT,
            url            TEXT NOT NULL UNIQUE,
            posted_on      TEXT,
            keywords       TEXT,
            score          INTEGER DEFAULT 0,
            score_reasoning TEXT,
            green_flags    TEXT,
            yellow_flags   TEXT,
            red_flags      TEXT,
            status         TEXT DEFAULT 'pending',
            found_at       TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS company_suggestions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            sector          TEXT,
            ats_type        TEXT,
            ats_tenant      TEXT,
            ats_career_site TEXT,
            career_url      TEXT,
            hq_location     TEXT,
            why_suggested   TEXT,
            status          TEXT DEFAULT 'pending',
            suggested_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS preference_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT,
            name       TEXT,
            company    TEXT,
            decision   TEXT,
            keywords   TEXT,
            score      INTEGER,
            reason     TEXT,
            logged_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS scan_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            company    TEXT,
            jobs_found INTEGER DEFAULT 0,
            jobs_new   INTEGER DEFAULT 0,
            error      TEXT
        );
    ''')
    # Seed default settings if not present
    defaults = {
        'score_threshold':        '6',
        'suggestion_interval_days': '2',
        'keywords_must_match':    json.dumps([
            'soc analyst','security analyst','siem','iam engineer',
            'vulnerability','detection engineer','security operations',
            'information security','cybersecurity','identity access',
            'incident response','cyber security'
        ]),
        'keywords_exclude':       json.dumps([
            'director','principal','staff engineer','vp ','vice president',
            'ciso','10+ years','15+ years','20+ years','clearance required',
            'secret clearance','top secret','travel 50%','travel required',
            'staffing','recruiter'
        ]),
        'active_sectors':         json.dumps([
            'healthcare_it','health_insurance','financial',
            'utilities','insurance','tech','government'
        ]),
        'last_suggestion_run':    '',
    }
    for k, v in defaults.items():
        conn.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)', (k, v))
    conn.commit()
    conn.close()

# ── Settings ──────────────────────────────────────────────────────────────────
def get_settings():
    conn = get_conn()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    s = {r['key']: r['value'] for r in rows}
    for k in ('keywords_must_match','keywords_exclude','active_sectors'):
        if k in s:
            try: s[k] = json.loads(s[k])
            except: s[k] = []
    return s

def save_setting(key, value):
    conn = get_conn()
    if isinstance(value, (list, dict)):
        value = json.dumps(value)
    conn.execute('INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)', (key, value))
    conn.commit()
    conn.close()

# ── Jobs ──────────────────────────────────────────────────────────────────────
def get_jobs(status_filter=None, keyword_filter=None, company_filter=None):
    conn = get_conn()
    q = 'SELECT * FROM jobs WHERE 1=1'
    p = []
    if status_filter and status_filter != 'all':
        q += ' AND status=?'; p.append(status_filter)
    if keyword_filter:
        q += ' AND (LOWER(title) LIKE ? OR LOWER(keywords) LIKE ?)'
        kw = f'%{keyword_filter.lower()}%'; p.extend([kw, kw])
    if company_filter and company_filter != 'all':
        q += ' AND company=?'; p.append(company_filter)
    q += ' ORDER BY found_at DESC'
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_status(job_id, status):
    conn = get_conn()
    conn.execute('UPDATE jobs SET status=?, seen=1 WHERE id=?', (status, job_id))
    conn.commit(); conn.close()

def mark_seen(job_id):
    conn = get_conn()
    conn.execute('UPDATE jobs SET seen=1 WHERE id=?', (job_id,))
    conn.commit(); conn.close()

def get_companies():
    conn = get_conn()
    rows = conn.execute('SELECT DISTINCT company FROM jobs ORDER BY company').fetchall()
    conn.close()
    return [r['company'] for r in rows]

def get_stats():
    conn = get_conn()
    total   = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    new     = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='new'").fetchone()[0]
    saved   = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='saved'").fetchone()[0]
    applied = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'").fetchone()[0]
    pend_j  = conn.execute("SELECT COUNT(*) FROM job_queue WHERE status='pending'").fetchone()[0]
    pend_c  = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='pending'").fetchone()[0]
    last    = conn.execute('SELECT scanned_at FROM scan_log ORDER BY scanned_at DESC LIMIT 1').fetchone()
    conn.close()
    return {'total': total, 'new': new, 'saved': saved, 'applied': applied,
            'pending_jobs': pend_j, 'pending_companies': pend_c,
            'last_scan': last['scanned_at'] if last else 'Never'}

# ── Job Queue ─────────────────────────────────────────────────────────────────
def queue_job(company, title, location, url, posted_on, keywords):
    """Save to queue if URL not seen before. Returns True if new."""
    conn = get_conn()
    exists = conn.execute('SELECT 1 FROM job_queue WHERE url=? UNION SELECT 1 FROM jobs WHERE url=?', (url, url)).fetchone()
    if exists:
        conn.close(); return False
    conn.execute(
        'INSERT INTO job_queue (company,title,location,url,posted_on,keywords) VALUES (?,?,?,?,?,?)',
        (company, title, location or 'See listing', url, posted_on, keywords)
    )
    conn.commit(); conn.close()
    return True

def get_pending_jobs(threshold=0):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM job_queue WHERE status='pending' AND score>=? ORDER BY score DESC, found_at DESC",
        (threshold,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unscored_jobs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM job_queue WHERE status='pending' AND score=0").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_job_score(job_id, score, reasoning, green, yellow, red):
    conn = get_conn()
    conn.execute(
        'UPDATE job_queue SET score=?,score_reasoning=?,green_flags=?,yellow_flags=?,red_flags=? WHERE id=?',
        (score, reasoning, json.dumps(green), json.dumps(yellow), json.dumps(red), job_id)
    )
    conn.commit(); conn.close()

def approve_job(job_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM job_queue WHERE id=?', (job_id,)).fetchone()
    if row:
        try:
            conn.execute(
                'INSERT INTO jobs (company,title,location,url,posted_on,keywords) VALUES (?,?,?,?,?,?)',
                (row['company'],row['title'],row['location'],row['url'],row['posted_on'],row['keywords'])
            )
        except: pass
        conn.execute("UPDATE job_queue SET status='approved' WHERE id=?", (job_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def reject_job(job_id, reason=''):
    conn = get_conn()
    row = conn.execute('SELECT * FROM job_queue WHERE id=?', (job_id,)).fetchone()
    if row:
        conn.execute("UPDATE job_queue SET status='rejected' WHERE id=?", (job_id,))
        conn.execute(
            'INSERT INTO preference_log (type,name,company,decision,keywords,score,reason) VALUES (?,?,?,?,?,?,?)',
            ('job', row['title'], row['company'], 'rejected', row['keywords'], row['score'], reason)
        )
        conn.commit()
    conn.close()

# ── Company Suggestions ───────────────────────────────────────────────────────
def save_company_suggestion(name, sector, ats_type, ats_tenant, ats_career_site, career_url, hq, why):
    conn = get_conn()
    try:
        conn.execute(
            '''INSERT OR IGNORE INTO company_suggestions
               (name,sector,ats_type,ats_tenant,ats_career_site,career_url,hq_location,why_suggested)
               VALUES (?,?,?,?,?,?,?,?)''',
            (name, sector, ats_type, ats_tenant, ats_career_site, career_url, hq, why)
        )
        conn.commit()
    except: pass
    conn.close()

def get_pending_companies():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM company_suggestions WHERE status='pending' ORDER BY suggested_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_company(company_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM company_suggestions WHERE id=?', (company_id,)).fetchone()
    if row:
        conn.execute("UPDATE company_suggestions SET status='approved' WHERE id=?", (company_id,))
        conn.execute(
            'INSERT INTO preference_log (type,name,decision,reason) VALUES (?,?,?,?)',
            ('company', row['name'], 'approved', row['sector'])
        )
        conn.commit()
    conn.close()
    return dict(row) if row else None

def reject_company(company_id, reason=''):
    conn = get_conn()
    row = conn.execute('SELECT * FROM company_suggestions WHERE id=?', (company_id,)).fetchone()
    if row:
        conn.execute("UPDATE company_suggestions SET status='rejected' WHERE id=?", (company_id,))
        conn.execute(
            'INSERT INTO preference_log (type,name,decision,reason) VALUES (?,?,?,?)',
            ('company', row['name'], 'rejected', reason or row['sector'])
        )
        conn.commit()
    conn.close()

def get_approved_companies():
    """Returns approved companies in scraper-ready format."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM company_suggestions WHERE status='approved'").fetchall()
    conn.close()
    companies = []
    for r in rows:
        r = dict(r)
        if r['ats_type'] == 'workday' and r['ats_tenant']:
            companies.append({'name': r['name'], 'type': 'workday',
                              'tenant': r['ats_tenant'], 'career_site': r['ats_career_site'] or ''})
        elif r['career_url']:
            companies.append({'name': r['name'], 'type': 'html',
                              'search_url': r['career_url'], 'fallback_url': r['career_url']})
    return companies

# ── Preference log helpers ────────────────────────────────────────────────────
def get_preference_summary(limit=20):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM preference_log ORDER BY logged_at DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    approved = [r['name'] for r in rows if r['decision'] == 'approved']
    rejected = [(r['name'], r['reason']) for r in rows if r['decision'] == 'rejected']
    return {'approved': approved, 'rejected': rejected}

def log_scan(company, found, new_count, error=None):
    conn = get_conn()
    conn.execute('INSERT INTO scan_log (company,jobs_found,jobs_new,error) VALUES (?,?,?,?)',
                 (company, found, new_count, error))
    conn.commit(); conn.close()

# ── Queue + preference tables ──────────────────────────────────────────────────
def init_queue_tables():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS company_suggestions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL UNIQUE,
            sector       TEXT,
            ats_type     TEXT DEFAULT 'Unknown',
            hq           TEXT,
            why_suggested TEXT,
            status       TEXT DEFAULT 'pending',
            suggested_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS job_queue (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            company      TEXT,
            title        TEXT,
            location     TEXT,
            url          TEXT UNIQUE,
            posted_on    TEXT,
            keywords     TEXT,
            score        INTEGER DEFAULT 0,
            score_reason TEXT,
            age_badge    TEXT,
            status       TEXT DEFAULT 'pending',
            found_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS preference_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            type      TEXT,
            name      TEXT,
            decision  TEXT,
            keywords  TEXT,
            sector    TEXT,
            notes     TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def get_pending_companies():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM company_suggestions WHERE status='pending' ORDER BY suggested_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pending_jobs(threshold=0):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM job_queue WHERE status='pending' AND score >= ? ORDER BY score DESC, found_at DESC",
        (threshold,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_company(company_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM company_suggestions WHERE id=?', (company_id,)).fetchone()
    if row:
        conn.execute("UPDATE company_suggestions SET status='approved' WHERE id=?", (company_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def reject_company(company_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM company_suggestions WHERE id=?', (company_id,)).fetchone()
    if row:
        conn.execute("UPDATE company_suggestions SET status='rejected' WHERE id=?", (company_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def approve_job(job_id):
    conn = get_conn()
    job = conn.execute('SELECT * FROM job_queue WHERE id=?', (job_id,)).fetchone()
    if job:
        conn.execute("UPDATE job_queue SET status='approved' WHERE id=?", (job_id,))
        # Move to main jobs table
        conn.execute(
            'INSERT OR IGNORE INTO jobs (company,title,location,url,posted_on,keywords,status) VALUES (?,?,?,?,?,?,?)',
            (job['company'], job['title'], job['location'], job['url'],
             job['posted_on'], job['keywords'], 'new')
        )
        conn.commit()
    conn.close()
    return dict(job) if job else None

def reject_job(job_id):
    conn = get_conn()
    job = conn.execute('SELECT * FROM job_queue WHERE id=?', (job_id,)).fetchone()
    if job:
        conn.execute("UPDATE job_queue SET status='rejected' WHERE id=?", (job_id,))
        conn.commit()
    conn.close()
    return dict(job) if job else None

def get_queue_counts():
    conn = get_conn()
    companies = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='pending'").fetchone()[0]
    jobs      = conn.execute("SELECT COUNT(*) FROM job_queue WHERE status='pending'").fetchone()[0]
    conn.close()
    return {'companies': companies, 'jobs': jobs}

# ── Approved companies table ───────────────────────────────────────────────────
def init_approved_companies():
    conn = get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS approved_companies (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            sector       TEXT,
            ats_type     TEXT DEFAULT 'Unknown',
            workday_tenant TEXT,
            careers_url  TEXT,
            hq           TEXT,
            why_added    TEXT,
            active       INTEGER DEFAULT 1,
            added_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            last_scanned TEXT
        )
    ''')
    # Also add new columns to company_suggestions if they don't exist
    for col, typedef in [
        ('careers_url',    'TEXT DEFAULT ""'),
        ('sample_roles',   'TEXT DEFAULT "[]"'),
        ('has_live_roles', 'INTEGER DEFAULT 0'),
        ('verified',       'INTEGER DEFAULT 0'),
        ('workday_tenant', 'TEXT DEFAULT ""'),
    ]:
        try:
            conn.execute(f'ALTER TABLE company_suggestions ADD COLUMN {col} {typedef}')
        except:
            pass
    conn.commit()
    conn.close()

def add_approved_company(suggestion_id):
    """Move a suggestion to approved_companies. Returns the company dict."""
    conn = get_conn()
    row = conn.execute(
        'SELECT * FROM company_suggestions WHERE id=?', (suggestion_id,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    row = dict(row)
    conn.execute("UPDATE company_suggestions SET status='approved' WHERE id=?", (suggestion_id,))
    conn.execute('''
        INSERT OR IGNORE INTO approved_companies
        (name, sector, ats_type, workday_tenant, careers_url, hq, why_added)
        VALUES (?,?,?,?,?,?,?)
    ''', (row['name'], row.get('sector',''), row.get('ats_type','Unknown'),
          row.get('workday_tenant',''), row.get('careers_url',''),
          row.get('hq',''), row.get('why_suggested','')))
    conn.commit()
    conn.close()
    return row

def get_approved_companies():
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM approved_companies WHERE active=1 ORDER BY name'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_last_scanned(company_name):
    conn = get_conn()
    conn.execute(
        "UPDATE approved_companies SET last_scanned=datetime('now') WHERE name=?",
        (company_name,)
    )
    conn.commit()
    conn.close()

# ── Company watchlist management ───────────────────────────────────────────────
def get_watchlist_companies():
    """All approved companies regardless of job status."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM company_suggestions WHERE status='approved' ORDER BY approved_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_active_companies():
    """Companies that have produced at least one relevant job."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM company_suggestions WHERE status='approved' AND total_jobs_found > 0 ORDER BY last_job_found DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_watching_companies():
    """Approved companies still in grace period with no jobs yet."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM company_suggestions WHERE status='approved' AND (total_jobs_found IS NULL OR total_jobs_found = 0) ORDER BY approved_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_auto_rejected_companies():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM company_suggestions WHERE status='auto_rejected' ORDER BY last_scanned DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def restore_company(company_id):
    """Restore an auto-rejected company back to watchlist."""
    conn = get_conn()
    conn.execute(
        "UPDATE company_suggestions SET status='approved', why_rejected=NULL, approved_at=datetime('now'), total_jobs_found=0 WHERE id=?",
        (company_id,)
    )
    conn.commit()
    conn.close()

def update_company_scan(company_id, jobs_found):
    """Update scan stats after a scrape run."""
    conn = get_conn()
    if jobs_found > 0:
        conn.execute('''
            UPDATE company_suggestions
            SET last_scanned=datetime('now'),
                last_job_found=datetime('now'),
                total_jobs_found=COALESCE(total_jobs_found,0)+?,
                scan_count=COALESCE(scan_count,0)+1
            WHERE id=?
        ''', (jobs_found, company_id))
    else:
        conn.execute('''
            UPDATE company_suggestions
            SET last_scanned=datetime('now'),
                scan_count=COALESCE(scan_count,0)+1
            WHERE id=?
        ''', (company_id,))
    conn.commit()
    conn.close()

def check_and_auto_reject(grace_days=14):
    """Auto-reject companies that exceeded grace period with zero relevant jobs."""
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=grace_days)).isoformat()
    conn = get_conn()
    candidates = conn.execute('''
        SELECT * FROM company_suggestions
        WHERE status='approved'
        AND (total_jobs_found IS NULL OR total_jobs_found = 0)
        AND approved_at IS NOT NULL
        AND approved_at < ?
    ''', (cutoff,)).fetchall()

    auto_rejected = []
    for co in candidates:
        days = (datetime.now() - datetime.fromisoformat(co['approved_at'])).days
        conn.execute('''
            UPDATE company_suggestions
            SET status='auto_rejected',
                why_rejected=?
            WHERE id=?
        ''', (f'No relevant listings found after {days} days of monitoring', co['id']))
        auto_rejected.append(dict(co))

    conn.commit()
    conn.close()
    return auto_rejected

def get_company_stats():
    conn = get_conn()
    total     = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status IN ('approved','auto_rejected')").fetchone()[0]
    active    = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='approved' AND total_jobs_found > 0").fetchone()[0]
    watching  = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='approved' AND (total_jobs_found IS NULL OR total_jobs_found=0)").fetchone()[0]
    rejected  = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='auto_rejected'").fetchone()[0]
    pending   = conn.execute("SELECT COUNT(*) FROM company_suggestions WHERE status='pending'").fetchone()[0]
    conn.close()
    return {
        'total': total, 'active': active,
        'watching': watching, 'rejected': rejected, 'pending': pending
    }
