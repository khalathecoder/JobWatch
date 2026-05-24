import requests, time, re, sqlite3, os
from bs4 import BeautifulSoup
from database import log_scan, update_company_scan, check_and_auto_reject
from suggestions import get_age_badge
from location_filter import location_qualifies, is_clearly_irrelevant_title

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
}

# ── Seed companies ─────────────────────────────────────────────────────────────
COMPANIES = [
    {'name': 'Cleveland Clinic',      'type': 'workday', 'tenant': 'clevelandclinic',  'career_site': 'ClevelandClinic_External_Career_Site'},
    {'name': 'Progressive Insurance', 'type': 'workday', 'tenant': 'progressive',      'career_site': 'ExtProgressive'},
    {'name': 'Elevance Health',       'type': 'workday', 'tenant': 'elevancehealth',   'career_site': 'ANT'},
    {'name': 'Humana',                'type': 'workday', 'tenant': 'humana',           'career_site': 'Humana_External_Careers'},
    {'name': 'UnitedHealth / Optum',  'type': 'workday', 'tenant': 'uhg',             'career_site': 'Optum_Careers'},
    {'name': 'FirstEnergy',           'type': 'workday', 'tenant': 'firstenergycorp', 'career_site': 'FE_External'},
    {'name': 'KeyBank',               'type': 'workday', 'tenant': 'key',             'career_site': 'Key_External_Career_Site'},
    {'name': 'Phreesia',              'type': 'workday', 'tenant': 'phreesia',         'career_site': 'Phreesia'},
    {'name': 'Owens & Minor',         'type': 'workday', 'tenant': 'owensminor',       'career_site': 'OMCareers'},
    {'name': 'CVS Health',            'type': 'workday', 'tenant': 'cvshealth',        'career_site': 'CVS_Health_External_Career_Site'},
    {'name': 'McKesson',              'type': 'workday', 'tenant': 'mckesson',         'career_site': 'McKesson_External_Career_Site'},
    {'name': 'Johnson & Johnson',     'type': 'workday', 'tenant': 'jnj',              'career_site': 'JNJ_External_Career_Site'},
    {'name': 'Medtronic',             'type': 'workday', 'tenant': 'medtronic',        'career_site': 'Medtronic_External_Career_Site'},
    {'name': 'University Hospitals',  'type': 'html',    'search_url': 'https://careers.uhhospitals.org/search/?q=security+analyst'},
    {'name': 'MetroHealth',           'type': 'html',    'search_url': 'https://jobs.metrohealth.org/search/?q=security'},
    {'name': 'iScribeHealth',         'type': 'html',    'search_url': 'https://www.iscribehealth.com/careers'},
]

def get_company_names():
    names = [c['name'] for c in COMPANIES]
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT name FROM company_suggestions WHERE status='approved'").fetchall()
    conn.close()
    names.extend(r[0] for r in rows)
    return names

# ── ATS detection ──────────────────────────────────────────────────────────────
def detect_ats(url, hint=''):
    u = (url or '').lower()
    h = (hint or '').lower()
    if 'myworkdayjobs' in u or 'workday' in u: return 'workday'
    if 'icims' in u:                            return 'icims'
    if 'greenhouse.io' in u:                   return 'greenhouse'
    if 'lever.co' in u:                        return 'lever'
    if 'taleo' in u:                           return 'taleo'
    if 'smartrecruiters' in u:                 return 'smartrecruiters'
    for ats in ('workday','icims','greenhouse','lever','taleo'):
        if ats in h: return ats
    return 'html'

def extract_workday_info(url):
    m = re.search(r'https://([^.]+)\.wd\d+\.myworkdayjobs\.com/wday/cxs/([^/]+)/([^/]+)/', url)
    if m: return m.group(1), m.group(3)
    m = re.search(r'https://([^.]+)\.wd\d+\.myworkdayjobs\.com/([^/?]+)', url)
    if m: return m.group(1), m.group(2)
    m = re.search(r'https://([^.]+)\.myworkdayjobs\.com/([^/?]+)', url)
    if m: return m.group(1), m.group(2)
    return None, None

def extract_board_token(url):
    m = re.search(r'greenhouse\.io/([^/?#]+)', url)
    if m: return m.group(1)
    m = re.search(r'lever\.co/([^/?#]+)', url)
    if m: return m.group(1)
    return None

# ── Keyword matching ───────────────────────────────────────────────────────────
SEARCH_TERMS = [
    'security analyst',
    'soc analyst',
    'siem',
    'iam engineer',
    'iam analyst',
    'vulnerability analyst',
    'vulnerability management',
    'detection engineer',
    'information security',
    'cybersecurity analyst',
    'cloud security',
    'devsecops',
    'identity access management',
    'security operations engineer',
    'application security',
    'compliance analyst',
    'production support engineer',
    'product support engineer',
    'application support engineer',
    'platform support engineer',
    'technical support engineer l3',
    'site reliability engineer',
]

SW_KEYWORDS = [
    'security', 'soc', 'siem', 'iam', 'vulnerability', 'detection',
    'cyber', 'analyst', 'engineer', 'developer', 'devops', 'cloud',
    'identity', 'access', 'compliance', 'risk', 'incident', 'threat',
    'endpoint', 'network security', 'application security',
    'production support', 'product support', 'application support',
    'platform support', 'sre', 'site reliability', 'azure monitor',
    'application insights', 'kql', 'troubleshooting', 'incident management',
]

def keyword_match(title, description=''):
    text = f"{title} {description or ''}".lower()
    found = [kw for kw in SW_KEYWORDS if kw in text]
    return ', '.join(found) if found else None

# ── Queue insertion ────────────────────────────────────────────────────────────
def queue_job(company, title, location, url, posted_on, keywords, description=''):
    """
    Multi-layer filter before queuing:
    1. Title relevance — catch obvious false positives
    2. Location — remote or Cleveland 50mi
    3. Basic SW keyword presence
    """
    from settings_db import get_excludes

    # Layer 1: Hard title disqualifier (Electrical Engineer, VP, etc.)
    irrelevant, reason = is_clearly_irrelevant_title(title)
    if irrelevant:
        return False

    # Layer 2: Exclude keywords (from settings)
    title_lower = title.lower()
    for ex in get_excludes():
        if ex.strip() and ex.strip().lower() in title_lower:
            return False

    # Layer 3: Location filter
    qualifies, loc_reason = location_qualifies(location)
    if not qualifies:
        return False

    # Layer 4: Must have at least one SW-relevant keyword in title OR description
    kw = keyword_match(title, description)
    if not kw:
        return False

    # Passed all filters — add to queue
    badge_emoji, _, badge_label = get_age_badge(posted_on)
    age_badge = f"{badge_emoji} {badge_label}"

    conn = sqlite3.connect(DB_PATH)
    for table in ('job_queue', 'jobs'):
        if conn.execute(f'SELECT id FROM {table} WHERE url=?', (url,)).fetchone():
            conn.close()
            return False

    # Truncate description to 1000 chars for storage
    desc_stored = (description or '')[:1000]

    conn.execute(
        '''INSERT INTO job_queue
           (company, title, location, url, posted_on, keywords, age_badge, description, location_raw)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (company, title, location or 'See listing', url, posted_on,
         kw, age_badge, desc_stored, location)
    )
    conn.commit()
    conn.close()
    return True

# ── Workday description fetcher ────────────────────────────────────────────────
def fetch_workday_description(base_url, external_path, tenant, career_site):
    """Fetch job description from Workday job detail endpoint."""
    try:
        api = f'{base_url}/wday/cxs/{tenant}/{career_site}/jobs/{external_path.strip("/")}'
        r = requests.get(api, headers={**HEADERS, 'Accept': 'application/json'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            desc = data.get('jobPostingInfo', {}).get('jobDescription', '')
            if desc:
                # Strip HTML tags
                soup = BeautifulSoup(desc, 'html.parser')
                return soup.get_text(separator=' ', strip=True)[:1000]
    except:
        pass
    return ''

# ── ATS scrapers ───────────────────────────────────────────────────────────────
def scrape_workday(name, tenant, career_site):
    base  = f'https://{tenant}.wd5.myworkdayjobs.com'
    api   = f'{base}/wday/cxs/{tenant}/{career_site}/jobs'
    found = new = 0

    for term in SEARCH_TERMS[:8]:  # Top 8 terms to keep it focused
        try:
            r = requests.post(api,
                json={'limit': 20, 'offset': 0, 'searchText': term},
                headers={**HEADERS, 'Content-Type': 'application/json'},
                timeout=15)
            if r.status_code != 200:
                continue
            for job in r.json().get('jobPostings', []):
                title    = job.get('title', '')
                path     = job.get('externalPath', '')
                location = job.get('locationsText', '')
                posted   = job.get('postedOn', '')
                url      = f'{base}{path}' if path else base

                # Quick pre-check before fetching description
                irrelevant, _ = is_clearly_irrelevant_title(title)
                if irrelevant:
                    continue

                loc_ok, _ = location_qualifies(location)
                if not loc_ok:
                    continue

                # Fetch description for better scoring accuracy
                description = fetch_workday_description(base, path, tenant, career_site)

                found += 1
                if queue_job(name, title, location, url, posted, None, description):
                    new += 1
            time.sleep(0.5)
        except Exception as e:
            print(f'  Workday error ({name}/{term}): {e}')

    return found, new

def scrape_greenhouse(name, board_token):
    url = f'https://api.greenhouse.io/v1/boards/{board_token}/jobs?content=true'
    found = new = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        for job in r.json().get('jobs', []):
            title    = job.get('title', '')
            job_url  = job.get('absolute_url', '')
            location = job.get('location', {}).get('name', '')
            updated  = job.get('updated_at', '')[:10]
            # Greenhouse includes full description
            desc_html = job.get('content', '')
            description = BeautifulSoup(desc_html, 'html.parser').get_text(' ', strip=True)[:1000] if desc_html else ''
            found += 1
            if queue_job(name, title, location, job_url, updated, None, description):
                new += 1
    except Exception as e:
        print(f'  Greenhouse error ({name}): {e}')
    return found, new

def scrape_lever(name, board_token):
    url = f'https://api.lever.co/v0/postings/{board_token}?mode=json'
    found = new = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        for job in r.json():
            title    = job.get('text', '')
            job_url  = job.get('hostedUrl', '')
            location = job.get('categories', {}).get('location', '')
            # Lever includes description
            desc_plain = job.get('descriptionPlain', '') or job.get('description', '')
            description = BeautifulSoup(desc_plain, 'html.parser').get_text(' ', strip=True)[:1000] if '<' in desc_plain else desc_plain[:1000]
            found += 1
            if queue_job(name, title, location, job_url, '', None, description):
                new += 1
    except Exception as e:
        print(f'  Lever error ({name}): {e}')
    return found, new

def scrape_html(name, search_url, fallback_url=None):
    found = new = 0
    url = search_url or fallback_url or ''
    try:
        r    = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        seen = set()
        for sel in ['a[href*="/jobs/"]','a[href*="/careers/"]','.iCIMS_JobTitle a','.job-title a','h2 a','h3 a']:
            for el in soup.select(sel):
                title = el.get_text(strip=True)
                href  = el.get('href', '')
                if not href or not title or len(title) < 5 or href in seen:
                    continue
                seen.add(href)
                base = url.split('/')[0] + '//' + url.split('/')[2]
                full = href if href.startswith('http') else base + href
                found += 1
                if queue_job(name, title, '', full, '', None, ''):
                    new += 1
    except Exception as e:
        print(f'  HTML error ({name}): {e}')
    return found, new

# ── Dynamic company router ─────────────────────────────────────────────────────
def scrape_dynamic_company(co):
    name = co['name']
    url  = co.get('careers_url') or ''
    ats  = detect_ats(url, co.get('ats_type',''))
    print(f'  [{ats.upper()}] {name}')
    if ats == 'workday':
        tenant, site = extract_workday_info(url)
        if tenant and site:
            return scrape_workday(name, tenant, site)
        print(f'    Could not parse Workday URL: {url}')
        return 0, 0
    elif ats == 'greenhouse':
        token = extract_board_token(url)
        return scrape_greenhouse(name, token) if token else (0, 0)
    elif ats == 'lever':
        token = extract_board_token(url)
        return scrape_lever(name, token) if token else (0, 0)
    else:
        return scrape_html(name, url)

# ── Company Discovery ──────────────────────────────────────────────────────────
def discover_new_companies():
    """
    Uses the 'Pro Researcher' mode via Manus API to find high-quality companies.
    Falls back to basic LLM discovery if Manus API key is missing.
    """
    import os
    if os.getenv('MANUS_API_KEY'):
        from manus_researcher import run_manus_discovery
        return run_manus_discovery()
    
    # Fallback to basic discovery if no API key
    from suggestions import call_claude, parse_json_response
    from database import get_conn
    
    print("  [DISCOVERY] (Fallback) Searching for new companies...")
    
    prompt = """
    Search for 5 large healthcare, finance, or technology companies that use Workday, Greenhouse, or Lever.
    Target companies must be relevant to this profile:
    - Name: Khala Wright (Security Analyst / Detection Engineer / Product Support Engineer)
    - Key Tools: SailPoint IIQ, CyberArk PAM, Microsoft Sentinel, Azure KQL, Wazuh SIEM, Application Insights.
    - Expertise: HIPAA compliance, IAM, SOC operations, .NET/Python automation, Application Support.
    - Preference: Fully remote roles in large enterprises (500+ employees).
    
    Return ONLY a valid JSON array of objects:
    [
      {
        "name": "Company Name",
        "sector": "healthcare",
        "ats_type": "workday",
        "careers_url": "https://company.wd5.myworkdayjobs.com/Careers"
      }
    ]
    """
    
    result = call_claude(prompt, use_search=True)
    if not result: return 0
    companies = parse_json_response(result)
    if not isinstance(companies, list): return 0
        
    conn = get_conn()
    added = 0
    for co in companies:
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO company_suggestions
                   (name, sector, ats_type, career_url, status)
                   VALUES (?,?,?,?,?)''',
                (co['name'], co['sector'], co['ats_type'], co['careers_url'], 'pending')
            )
            added += 1
        except: pass
    
    conn.commit()
    conn.close()
    return added

# ── Main run ───────────────────────────────────────────────────────────────────
def run_scrape(company_name=None, discover=False):
    if discover:
        discover_new_companies()

    from settings_db import get_grace_days
    results = []

    # Static seed companies
    targets = COMPANIES if not company_name else [c for c in COMPANIES if c['name'] == company_name]
    for co in targets:
        print(f'  [STATIC/{co["type"].upper()}] {co["name"]}')
        if co['type'] == 'workday':
            found, new = scrape_workday(co['name'], co['tenant'], co['career_site'])
        else:
            found, new = scrape_html(co['name'], co.get('search_url'), co.get('fallback_url'))
        log_scan(co['name'], found, new)
        results.append({'company': co['name'], 'found': found, 'new': new})
        time.sleep(1)

    # Dynamic watchlist companies
    if not company_name or not any(c['name'] == company_name for c in COMPANIES):
        conn = sqlite3.connect(DB_PATH)
        q = "SELECT * FROM company_suggestions WHERE status='approved'"
        if company_name:
            q += f" AND name='{company_name}'"
        watchlist = conn.execute(q).fetchall()
        conn.close()
        for row in watchlist:
            co = dict(row)
            found, new = scrape_dynamic_company(co)
            log_scan(co['name'], found, new)
            update_company_scan(co['id'], new)
            results.append({'company': co['name'], 'found': found, 'new': new})
            time.sleep(1)

    # Grace period check on full runs
    if not company_name:
        auto_rejected = check_and_auto_reject(get_grace_days())
        if auto_rejected:
            print(f'\n  Auto-rejected {len(auto_rejected)} companies with no relevant listings')

    return results

def run_company_scan(company_id):
    """Immediate scan for a newly approved company."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT * FROM company_suggestions WHERE id=?', (company_id,)).fetchone()
    conn.close()
    if not row:
        return
    co = dict(row)
    print(f'\n  Immediate scan: {co["name"]}')
    found, new = scrape_dynamic_company(co)
    log_scan(co['name'], found, new)
    update_company_scan(company_id, new)
    print(f'  → {found} processed, {new} new jobs queued')
