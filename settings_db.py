"""
Settings helpers — thin wrapper over the settings table in database.py.
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

DEFAULTS = {
    'archive_after_days':  '14',
    'score_threshold':     '6',
    'suggestion_interval': '2',
    'company_grace_days':  '14',
    'sectors':             'healthcare,financial,utilities,insurance,government,tech',
    'must_match': (
        'soc analyst,security analyst,siem,iam engineer,iam analyst,'
        'vulnerability,detection engineer,information security,cybersecurity,'
        'identity access,endpoint security,security engineer,cloud security,'
        'devsecops,compliance analyst,application security,risk analyst,'
        'production support,security operations,site reliability,sre'
    ),
    'exclude': (
        'electrical engineer,civil engineer,mechanical engineer,hvac,'
        'facilities engineer,hardware engineer,clearance required,'
        'ts/sci,active clearance,top secret,polygraph,'
        'director,vice president,ciso,chief '
    ),
}


def _get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_settings():
    """Seed default settings into the DB if not already present."""
    conn = _get_conn()
    conn.execute(
        'CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT DEFAULT "")'
    )
    for k, v in DEFAULTS.items():
        conn.execute('INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)', (k, v))
    conn.commit()
    conn.close()


def get_all():
    conn = _get_conn()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    result = dict(DEFAULTS)
    result.update({r['key']: r['value'] for r in rows})
    return result


def get(key):
    conn = _get_conn()
    row = conn.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else DEFAULTS.get(key, '')


def set(key, value):
    conn = _get_conn()
    conn.execute('INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)', (key, str(value)))
    conn.commit()
    conn.close()


def save_all(data: dict):
    conn = _get_conn()
    for k, v in data.items():
        conn.execute('INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)', (k, v))
    conn.commit()
    conn.close()


def get_sectors():
    return [s.strip() for s in get('sectors').split(',') if s.strip()]


def get_must_match():
    return [k.strip().lower() for k in get('must_match').split(',') if k.strip()]


def get_excludes():
    return [k.strip().lower() for k in get('exclude').split(',') if k.strip()]


def get_grace_days():
    try:
        return int(get('company_grace_days') or 14)
    except ValueError:
        return 14
