import os, json, requests, sqlite3, re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobwatch.db')

def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

# ── Claude API ────────────────────────────────────────────────────────────────
def call_claude(prompt, system='', use_search=False):
    key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not key:
        return None
    headers = {
        'x-api-key': key,
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    body = {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 2000,
        'system': system or 'Return only valid JSON. No markdown fences, no explanation.',
        'messages': [{'role': 'user', 'content': prompt}]
    }
    if use_search:
        body['tools'] = [{'type': 'web_search_20250305', 'name': 'web_search'}]
        body['max_tokens'] = 4000
    try:
        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            json=body, headers=headers, timeout=60
        )
        data = r.json()
        # Collect all text blocks (web search may produce multiple)
        texts = [b['text'] for b in data.get('content', []) if b.get('type') == 'text']
        return '\n'.join(texts) if texts else None
    except Exception as e:
        print(f'Claude API error: {e}')
        return None

def parse_json_response(text):
    if not text:
        return None
    text = text.strip()
    # Strip markdown fences if present
    text = re.sub(r'```(?:json)?', '', text).strip('`').strip()
    # Find first [ or { and last ] or }
    start = min(
        (text.find('[') if text.find('[') >= 0 else len(text)),
        (text.find('{') if text.find('{') >= 0 else len(text))
    )
    end = max(text.rfind(']'), text.rfind('}'))
    if start <= end:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except Exception as e:
        print(f'JSON parse error: {e}\nText: {text[:300]}')
        return None

# ── Date + Age badges ─────────────────────────────────────────────────────────
def parse_posted_date(s):
    if not s:
        return None
    s = str(s).lower().strip()
    now = datetime.now()
    if 'today' in s:
        return now
    if 'yesterday' in s:
        return now - timedelta(days=1)
    m = re.search(r'(\d+)\+?\s*days?\s*ago', s)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r'(\d+)\+?\s*months?\s*ago', s)
    if m:
        return now - timedelta(days=int(m.group(1)) * 30)
    try:
        return datetime.fromisoformat(str(s)[:10])
    except:
        return None

def get_age_badge(posted_str):
    dt = parse_posted_date(posted_str)
    if not dt:
        return ('❓', 'age-unknown', 'Date unknown')
    age = (datetime.now() - dt).days
    if age <= 2:  return ('🔥', 'age-fire',   f'{"Today" if age==0 else "Yesterday" if age==1 else f"{age}d ago"}')
    if age <= 7:  return ('🟢', 'age-fresh',  f'{age}d ago')
    if age <= 14: return ('🟡', 'age-recent', f'{age}d ago')
    if age <= 30: return ('🔴', 'age-aging',  f'{age}d ago')
    return ('👻', 'age-stale', f'{age}+ days ago')

def should_archive(posted_str, threshold_days):
    dt = parse_posted_date(posted_str)
    if not dt:
        return False
    return (datetime.now() - dt).days > int(threshold_days)

# ── Preference history ─────────────────────────────────────────────────────────
def get_preference_history(limit=20):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM preference_log ORDER BY logged_at DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    approved = [dict(r) for r in rows if r['decision'] == 'approved']
    rejected = [dict(r) for r in rows if r['decision'] == 'rejected']
    return approved, rejected

def log_preference(ptype, name, decision, keywords='', sector='', notes=''):
    conn = get_conn()
    conn.execute(
        'INSERT INTO preference_log (type,name,decision,keywords,sector,notes) VALUES (?,?,?,?,?,?)',
        (ptype, name, decision, keywords, sector, notes)
    )
    conn.commit()
    conn.close()

# ── Company suggestions ────────────────────────────────────────────────────────
def get_existing_companies():
    conn = get_conn()
    rows = conn.execute(
        "SELECT name FROM company_suggestions WHERE status IN ('approved','pending')"
    ).fetchall()
    conn.close()
    from scraper import COMPANIES
    existing = {c['name'] for c in COMPANIES}
    existing.update(r['name'] for r in rows)
    return list(existing)

def suggest_companies(sectors):
    existing  = get_existing_companies()
    approved, rejected = get_preference_history()

    approved_names  = ', '.join(r['name'] for r in approved  if r['type']=='company')[:200] or 'None yet'
    rejected_names  = ', '.join(r['name'] for r in rejected  if r['type']=='company')[:200] or 'None yet'
    approved_notes  = '; '.join(
        f"{r['name']} ({r.get('notes','')})" for r in approved if r['type']=='company'
    )[:300] or 'None yet'

    prompt = f"""I need you to suggest companies for a cybersecurity and product support job seeker. Use web search to find real, accurate information about each company's careers page and recent job postings.
	
	CANDIDATE PROFILE:
	- Name: Khala Wright
	- Target Roles: Security Analyst, Detection Engineer, SIEM & Compliance Specialist, Product Support Engineer, Application Support Engineer.
	- Experience: 3+ years at Solventum (formerly 3M Health) and iScriptServices.
	- Key Expertise: Investigating application security events, remediating IAM and access control violations, enforcing HIPAA compliance, and performing high-level application/production support.
	- Tools (Security): SailPoint IIQ, CyberArk PAM, Microsoft Sentinel, Tenable/Nessus, Defender for Endpoint, Wazuh SIEM, Burp Suite.
	- Tools (Cloud/Dev): Microsoft Azure (App Services, Application Insights, KQL, Storage), IIS, CI/CD pipelines, .NET/ASP.NET Core, Blazor.
	- Languages: C#, Python, PowerShell, Bash, SQL, JavaScript, TypeScript.
	- Certifications: CompTIA CySA+, CompTIA PenTest+.
	- Education: M.S. Cybersecurity & Information Assurance (WGU, May 2026).
	- Specific Project: Built "DataPulse", a DSPM tool integrating Wazuh SIEM for HIPAA violation scanning.
	- Salary target: $85,000 - $120,000
	- Location: Cleveland Heights, OH — FULLY REMOTE only (no hybrid, no onsite)
	- Prefers: Internal security or product support teams at enterprise companies (500+ employees), especially in healthcare, finance, or tech. Avoid staffing agencies or MSSPs.

DO NOT SUGGEST:
- MSSPs, managed security providers, or IT staffing agencies
- Consulting firms requiring significant travel (>10%)
- Companies requiring US security clearance
- Companies known to pay significantly below market
- Companies in these lists: {', '.join(existing[:15])}

PREVIOUSLY APPROVED (these fit her well — find similar):
{approved_notes}

PREVIOUSLY REJECTED (avoid these patterns):
{rejected_names}

TARGET SECTORS: {', '.join(sectors)}

TASK: Search for 6 companies that:
1. Operate in the target sectors above
2. Post IAM, SIEM, SOC Analyst, Security Analyst, or similar security roles
3. Are remote-friendly (check their job postings for remote options)
4. Use a recognizable ATS (Workday, iCIMS, Greenhouse, Lever, Taleo, SmartRecruiters)
5. Are likely to value SailPoint, CyberArk, and healthcare compliance experience

For each company:
- Search their actual careers page
- Confirm they have posted at least one security-related role in the past 6 months OR are large enough that it's highly probable
- Get the exact careers page URL

Return ONLY a valid JSON array, nothing else:
[{{
  "name": "Company Name",
  "sector": "healthcare",
  "ats_type": "Workday",
  "careers_url": "https://company.wd5.myworkdayjobs.com/careers",
  "hq": "City, ST",
  "remote_friendly": true,
  "why": "Specific 1-sentence reason this fits her — mention tools, sector, or known hiring patterns"
}}]"""

    result = call_claude(prompt, use_search=True)
    if not result:
        return []
    data = parse_json_response(result)
    return data if isinstance(data, list) else []

def run_company_suggestions():
    from settings_db import get_sectors
    companies = suggest_companies(get_sectors())
    if not companies:
        return 0

    # Ensure careers_url column exists
    conn = get_conn()
    try:
        conn.execute('ALTER TABLE company_suggestions ADD COLUMN careers_url TEXT')
        conn.commit()
    except:
        pass  # Column already exists

    added = 0
    for c in companies:
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO company_suggestions
                   (name, sector, ats_type, careers_url, hq, why_suggested)
                   VALUES (?,?,?,?,?,?)''',
                (c.get('name',''), c.get('sector',''), c.get('ats_type','Unknown'),
                 c.get('careers_url',''), c.get('hq',''), c.get('why',''))
            )
            added += 1
        except Exception as e:
            print(f'Insert error: {e}')
    conn.commit()
    conn.close()
    return added

# ── Job scoring ────────────────────────────────────────────────────────────────
def score_job(title, company, keywords, description=''):
    approved, rejected = get_preference_history(limit=15)

    approved_jobs = [r for r in approved if r['type'] == 'job']
    rejected_jobs = [r for r in rejected if r['type'] == 'job']

    approved_ex = '; '.join(
        f"{r['name']} — {r.get('notes','')}" for r in approved_jobs[:5]
    ) or 'None yet'
    rejected_ex = '; '.join(
        f"{r['name']} — {r.get('keywords','')}" for r in rejected_jobs[:5]
    ) or 'None yet'

    desc_section = f"""
Job Description (first 600 chars):
{description[:600] if description else "Not available — score based on title and keywords only"}
""" if description else "Job description not available."

    prompt = f"""Score this job 1-10 for this candidate. Use the description to verify the role is relevant to her software/security or product support background.
	
	CANDIDATE PROFILE:
	- Production Support Engineer (Current) pivoting to cybersecurity.
	- Daily tools: SailPoint IIQ, CyberArk PAM, Microsoft Sentinel, Azure KQL/App Insights, Tenable/Nessus, Defender for Endpoint, Wazuh SIEM.
	- Dev skills: C#/.NET, Python, PowerShell, Bash, SQL Server, Azure (App Services, IIS).
	- Certs: CompTIA CySA+, CompTIA PenTest+, M.S. Cybersecurity (WGU 2026).
	- Background: HIPAA compliance, healthcare IT, IAM workflows, incident investigation, log analysis, high-level production support.
	- Target salary: $85k-$120k
	- Location: Cleveland Heights OH — wants REMOTE or within 50 miles of Cleveland.
	
	HARD DOWN-SCORE RULES — only these warrant a 1-3 score:
	- Active security clearance required (TS, Secret, TS/SCI, Polygraph) → score 1-2.
	- On-site only with no remote option AND not in Cleveland/NE Ohio area → score 1-3.
	- Title contains Director, VP, CISO, Chief, SVP, EVP → score 1-2.
	- Description reveals non-SW role (electrical, mechanical, civil, HVAC, facilities) → score 1.
	
	SCORE NORMALLY — do NOT penalize these:
	- MSSPs and managed security providers → score on role quality.
	- Staffing agencies / contract placements → score the role itself.
	- Tier 1 SOC Analyst title → read description for actual responsibilities.
	- Senior Product/Production Support roles → she is highly qualified for these.
	
	UP-SCORE FACTORS:
	- Mentions SailPoint, CyberArk, Azure, HIPAA, healthcare → +1-2 points each.
	- Explicitly remote or Cleveland/Ohio location → +1 point.
	- IAM, SIEM, SOC, detection engineering focus → +2 points.
	- Production/Product Support Engineer roles matching her Azure/KQL/Support background → +2 points.
	- Similar to previously approved jobs → +1-2 points.

PREVIOUSLY APPROVED JOBS (she liked these):
{approved_ex}

PREVIOUSLY REJECTED JOBS (she skipped these):
{rejected_ex}

JOB TO SCORE:
Title: {title}
Company: {company}
Keywords matched: {keywords or 'None detected'}
{desc_section}

Return ONLY valid JSON — no explanation outside it:
{{"score": 7, "reason": "Specific 1-sentence reason referencing the description or her tools"}}"""

    result = call_claude(prompt)
    if not result:
        return 5, 'API unavailable'
    data = parse_json_response(result)
    if not data or not isinstance(data, dict):
        return 5, 'Could not parse score'
    score = max(1, min(10, int(data.get('score', 5))))
    return score, data.get('reason', '')


def score_pending_jobs():
    conn = get_conn()
    pending = conn.execute(
        "SELECT * FROM job_queue WHERE (score IS NULL OR score = 0) AND status='pending' LIMIT 25"
    ).fetchall()
    conn.close()
    for job in pending:
        score, reason = score_job(job['title'], job['company'], job['keywords'] or '', job['description'] or '')
        conn = get_conn()
        conn.execute(
            'UPDATE job_queue SET score=?, score_reason=? WHERE id=?',
            (score, reason, job['id'])
        )
        conn.commit()
        conn.close()
