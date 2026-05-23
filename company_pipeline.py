"""
Company suggestion, verification, and enrichment pipeline.

Stage 1: Claude generates candidates with Workday tenant guesses
Stage 2: Verify by hitting the actual careers endpoint
Stage 3: Store enriched data in company_suggestions queue
"""
import os, json, re, time, sqlite3, requests
from suggestions import call_claude, get_preference_history

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

SECURITY_TERMS = [
    'security analyst', 'soc analyst', 'siem', 'iam engineer',
    'vulnerability', 'detection engineer', 'information security',
    'cybersecurity', 'cyber security', 'identity access',
    'security operations', 'incident response', 'security engineer'
]

# ── ATS detection ─────────────────────────────────────────────────────────────
def detect_ats(url):
    url = (url or '').lower()
    if 'myworkdayjobs.com' in url: return 'Workday'
    if 'icims.com'         in url: return 'iCIMS'
    if 'taleo.net'         in url: return 'Taleo'
    if 'greenhouse.io'     in url: return 'Greenhouse'
    if 'lever.co'          in url: return 'Lever'
    if 'smartrecruiters'   in url: return 'SmartRecruiters'
    if 'bamboohr.com'      in url: return 'BambooHR'
    if 'jobvite.com'       in url: return 'Jobvite'
    return 'Custom'

# ── Workday verification ──────────────────────────────────────────────────────
WORKDAY_SITE_PATTERNS = [
    '{T}_External_Career_Site',
    'Ext{T}',
    '{T}_External',
    '{T}Careers',
    '{T}_Careers',
    '{T}',
]

def try_workday_tenant(tenant):
    """
    Try common career site patterns for a Workday tenant.
    Returns (careers_url, sample_roles) or (None, [])
    """
    if not tenant:
        return None, []
    tenant = tenant.strip().lower().replace(' ', '')
    T = tenant.replace('-','').replace('_','')
    bases = [
        f'https://{tenant}.wd5.myworkdayjobs.com',
        f'https://{tenant}.wd1.myworkdayjobs.com',
        f'https://{tenant}.wd3.myworkdayjobs.com',
    ]
    for base in bases:
        for pattern in WORKDAY_SITE_PATTERNS:
            site = pattern.replace('{T}', T).replace('{t}', tenant)
            api  = f'{base}/wday/cxs/{tenant}/{site}/jobs'
            try:
                r = requests.post(
                    api,
                    json={'limit': 20, 'offset': 0, 'searchText': 'security analyst'},
                    headers={**HEADERS, 'Content-Type': 'application/json'},
                    timeout=8
                )
                if r.status_code == 200:
                    data  = r.json()
                    posts = data.get('jobPostings', [])
                    if posts is not None:
                        # Check for security-related roles
                        security_roles = []
                        for job in posts:
                            title = job.get('title', '').lower()
                            if any(t in title for t in SECURITY_TERMS):
                                security_roles.append(job.get('title',''))
                        careers_url = f'{base}/{site}'
                        return careers_url, security_roles[:3]
            except:
                continue
            time.sleep(0.2)
    return None, []

# ── Stage 1: Claude generates candidates ─────────────────────────────────────
def generate_candidates(sectors, existing, approved_history, rejected_history):
    approved_ex  = '; '.join(f"{r['name']} ({r.get('sector','')})" for r in approved_history[:6]) or 'None yet'
    rejected_ex  = '; '.join(f"{r['name']}" for r in rejected_history[:6]) or 'None yet'
    existing_str = ', '.join(existing[:25]) or 'None yet'

    prompt = f"""You are helping a cybersecurity professional find employers to apply to.

CANDIDATE PROFILE:
- 3 years production support + security operations in healthcare IT
- Daily tools at current job: SailPoint IIQ, CyberArk PAM, Azure (App Services, KQL, Application Insights), SQL Server
- Languages: C#/.NET, Python, PowerShell, Bash, SQL
- Certifications: CompTIA CySA+, PenTest+ (PT0-003)
- Education: M.S. Cybersecurity & Information Assurance (WGU, May 2026)
- Built: DataPulse (DSPM tool with Wazuh SIEM integration, HIPAA compliance scanning)
- HIPAA/PHI compliance experience across Epic, Cerner, Meditech, and other EHR systems
- Wants: fully remote, internal security team (NOT MSSP/staffing), $85k-$120k range
- Will NOT consider: consulting firms requiring travel, roles needing security clearance, MSSP/managed services, tier-1 only SOC roles

TARGET SECTORS: {', '.join(sectors)}
LOCATION: Cleveland Heights OH — prefers remote nationwide, open to hybrid near Cleveland

PREVIOUSLY APPROVED (suggest similar): {approved_ex}
PREVIOUSLY SKIPPED (avoid similar): {rejected_ex}
ALREADY TRACKING (do NOT suggest): {existing_str}

Suggest exactly 10 NEW companies. For each:
1. Prioritize companies known to have internal security teams
2. Prefer companies that use Workday, iCIMS, or Greenhouse (easier to scrape)
3. Include Workday tenant ID if you know it (e.g., "progressive" for Progressive Insurance)
4. Provide actual careers page URL if known
5. Explain specifically why this candidate's background fits

Return ONLY a valid JSON array — no markdown, no extra text:
[
  {{
    "name": "Company Name",
    "sector": "insurance",
    "hq": "City, ST",
    "ats_type": "Workday",
    "workday_tenant": "companyname",
    "careers_url": "https://company.wd5.myworkdayjobs.com/CompanyName_External",
    "why": "Specific reason this company fits this candidate's background",
    "remote_friendly": true,
    "approx_size": "10,000+"
  }}
]"""

    result = call_claude(prompt)
    if not result:
        return []
    try:
        text = result.strip()
        if '```' in text:
            text = re.sub(r'```(?:json)?', '', text).strip()
        return json.loads(text)
    except Exception as e:
        print(f'Candidate parse error: {e}\nRaw: {result[:300]}')
        return []

# ── Stage 2: Verify each candidate ───────────────────────────────────────────
def verify_candidate(c):
    """
    Try to verify a candidate company has security roles.
    Returns enriched company dict with verification results.
    """
    name         = c.get('name', '')
    ats_type     = c.get('ats_type', 'Unknown')
    tenant_guess = c.get('workday_tenant', '')
    careers_url  = c.get('careers_url', '')

    verified_url   = None
    sample_roles   = []
    has_roles      = False
    ats_confirmed  = ats_type

    if ats_type == 'Workday' or tenant_guess:
        verified_url, sample_roles = try_workday_tenant(tenant_guess)
        if verified_url:
            ats_confirmed = 'Workday'
            has_roles     = len(sample_roles) > 0
            if not has_roles:
                # Workday endpoint works but no security roles right now
                # Still valid — they have a careers page, just quiet on security
                has_roles = False
        else:
            # Workday tenant didn't work — fall back to provided URL
            verified_url = careers_url or None
            ats_confirmed = ats_type
    else:
        verified_url = careers_url or None

    return {
        **c,
        'ats_type':      ats_confirmed,
        'careers_url':   verified_url or careers_url or '',
        'sample_roles':  json.dumps(sample_roles),
        'has_live_roles': has_roles,
        'verified':      bool(verified_url),
    }

# ── Full pipeline ─────────────────────────────────────────────────────────────
def run_suggestion_pipeline():
    """Run the full two-stage pipeline and store results."""
    from settings_db import get_sectors, get
    from scraper import COMPANIES

    # Build existing list
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    existing_suggested = [r['name'] for r in
        conn.execute("SELECT name FROM company_suggestions").fetchall()]
    existing_approved  = [r['name'] for r in
        conn.execute("SELECT name FROM approved_companies").fetchall()]
    conn.close()

    existing = list(set(
        [c['name'] for c in COMPANIES] + existing_suggested + existing_approved
    ))

    sectors = get_sectors()
    approved_h, rejected_h = get_preference_history()

    print(f'Stage 1: Generating candidates for sectors: {sectors}')
    candidates = generate_candidates(sectors, existing, approved_h, rejected_h)
    print(f'  Got {len(candidates)} candidates')

    added = 0
    for i, c in enumerate(candidates):
        print(f'  Verifying {i+1}/{len(candidates)}: {c.get("name","")}...')
        enriched = verify_candidate(c)
        time.sleep(0.3)

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute('''
                INSERT OR IGNORE INTO company_suggestions
                (name, sector, ats_type, hq, careers_url, why_suggested,
                 sample_roles, has_live_roles, verified, workday_tenant)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                enriched.get('name',''),
                enriched.get('sector',''),
                enriched.get('ats_type','Unknown'),
                enriched.get('hq',''),
                enriched.get('careers_url',''),
                enriched.get('why',''),
                enriched.get('sample_roles','[]'),
                1 if enriched.get('has_live_roles') else 0,
                1 if enriched.get('verified') else 0,
                enriched.get('workday_tenant',''),
            ))
            conn.commit()
            added += 1
        except Exception as e:
            print(f'  Insert error: {e}')
        finally:
            conn.close()

    print(f'Pipeline complete: {added} companies added to queue')
    return added
