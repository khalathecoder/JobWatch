import sqlite3, json, os
from profile_data import PROFILE_INFO, SUMMARIES, EXPERIENCE, EDUCATION, SKILLS, CERTIFICATIONS

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_profile_tables():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS profile_info (
            key   TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS profile_summary (
            resume_version TEXT PRIMARY KEY,
            summary        TEXT DEFAULT '',
            passion_statement TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS experience (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT DEFAULT 'both',
            job_title      TEXT,
            company        TEXT,
            start_date     TEXT,
            end_date       TEXT,
            responsibilities TEXT DEFAULT '[]',
            sort_order     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS education (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            degree         TEXT,
            school         TEXT,
            graduation_date TEXT,
            sort_order     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS skills (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_version TEXT DEFAULT 'both',
            category       TEXT,
            items          TEXT
        );
        CREATE TABLE IF NOT EXISTS certifications (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        );
    ''')
    conn.commit()

    # Seed only if tables are empty
    if not conn.execute('SELECT 1 FROM profile_info LIMIT 1').fetchone():
        for k, v in PROFILE_INFO.items():
            conn.execute('INSERT OR IGNORE INTO profile_info (key, value) VALUES (?,?)', (k, v))
        for version, text in SUMMARIES.items():
            conn.execute('INSERT OR IGNORE INTO profile_summary (resume_version, summary, passion_statement) VALUES (?,?,?)', (version, text, ''))
        for i, exp in enumerate(EXPERIENCE):
            conn.execute(
                'INSERT INTO experience (resume_version, job_title, company, start_date, end_date, responsibilities, sort_order) VALUES (?,?,?,?,?,?,?)',
                (exp['resume'], exp['title'], exp['company'], exp['start'], exp['end'], json.dumps(exp['bullets']), i)
            )
        for i, edu in enumerate(EDUCATION):
            conn.execute(
                'INSERT INTO education (degree, school, graduation_date, sort_order) VALUES (?,?,?,?)',
                (edu['degree'], edu['school'], edu['date'], i)
            )
        for version, cats in SKILLS.items():
            for cat, items in cats.items():
                conn.execute(
                    'INSERT INTO skills (resume_version, category, items) VALUES (?,?,?)',
                    (version, cat, items)
                )
        for cert in CERTIFICATIONS:
            conn.execute('INSERT INTO certifications (name) VALUES (?)', (cert,))
        conn.commit()
    conn.close()

def get_profile():
    conn = get_conn()
    info  = {r['key']: r['value'] for r in conn.execute('SELECT * FROM profile_info').fetchall()}
    sums_raw = conn.execute('SELECT * FROM profile_summary').fetchall()
    sums  = {r['resume_version']: r['summary'] for r in sums_raw if r['resume_version'] != 'passion'}
    # Get passion statement separately
    passion_row = conn.execute("SELECT passion_statement FROM profile_summary WHERE resume_version='passion'").fetchone()
    passion = passion_row['passion_statement'] if passion_row else ''
    exps  = []
    for r in conn.execute('SELECT * FROM experience ORDER BY sort_order').fetchall():
        d = dict(r)
        d['responsibilities'] = json.loads(d['responsibilities'])
        exps.append(d)
    edus  = [dict(r) for r in conn.execute('SELECT * FROM education ORDER BY sort_order').fetchall()]
    skills_raw = conn.execute('SELECT * FROM skills ORDER BY resume_version, id').fetchall()
    skills = {'A': {}, 'B': {}, 'both': {}}
    for r in skills_raw:
        skills[r['resume_version']][r['category']] = r['items']
    certs = [r['name'] for r in conn.execute('SELECT * FROM certifications').fetchall()]
    conn.close()
    return {'info': info, 'summaries': sums, 'passion': passion, 'experience': exps,
            'education': edus, 'skills': skills, 'certifications': certs}

def save_profile_info(data: dict):
    conn = get_conn()
    for k, v in data.items():
        conn.execute('INSERT OR REPLACE INTO profile_info (key, value) VALUES (?,?)', (k, v))
    conn.commit()
    conn.close()

def save_summary(version, text):
    conn = get_conn()
    conn.execute('INSERT OR REPLACE INTO profile_summary (resume_version, summary, passion_statement) VALUES (?,?,?)', (version, text, ''))
    conn.commit()
    conn.close()

def save_experience(exp_id, data):
    conn = get_conn()
    bullets = json.dumps(data.get('responsibilities', []))
    conn.execute('''UPDATE experience SET job_title=?, company=?, start_date=?, end_date=?,
                    responsibilities=?, resume_version=? WHERE id=?''',
        (data['job_title'], data['company'], data['start_date'],
         data['end_date'], bullets, data['resume_version'], exp_id))
    conn.commit()
    conn.close()

def save_passion(text):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO profile_summary (resume_version, summary, passion_statement) VALUES ('passion', '', ?)",
        (text,)
    )
    conn.commit()
    conn.close()
