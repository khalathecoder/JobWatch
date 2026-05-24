import os, sys, sqlite3, json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import (init_db, init_queue_tables, get_jobs, update_status, mark_seen, mark_expired,
                      get_companies, get_stats, get_pending_companies, get_pending_jobs,
                      approve_company, reject_company, approve_job, reject_job,
                      get_active_companies, get_watching_companies, get_auto_rejected_companies,
                      restore_company, init_approved_companies, add_approved_company,
                      save_web_job, get_web_saves, update_web_save_status,
                      log_scan, update_company_scan, get_unscored_jobs, update_job_score,
                      queue_job, save_company_suggestion, get_preference_summary)
from scraper import run_scrape, get_company_names, run_company_scan
from profile_db import init_profile_tables, get_profile, save_profile_info, save_summary, save_experience, save_passion
from settings_db import init_settings, get_all as get_settings, save_all as save_settings, get
from suggestions import score_pending_jobs, log_preference
from company_pipeline import run_suggestion_pipeline
from extension_api import extension_api, set_extension_token

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-change-this')

# Custom Jinja filter for parsing JSON in templates
import json as _json
@app.template_filter('from_json')
def from_json_filter(s):
    try: return _json.loads(s or '[]')
    except: return []

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = ''

USERNAME      = os.environ.get('DASHBOARD_USERNAME', 'khala')
PASSWORD_HASH = generate_password_hash(os.environ.get('DASHBOARD_PASSWORD', 'changeme'))
EXTENSION_TOKEN = os.environ.get('EXTENSION_TOKEN', 'jobwatch-local')

# Set extension token
set_extension_token(EXTENSION_TOKEN)

class User(UserMixin):
    id = 'owner'
OWNER = User()

@login_manager.user_loader
def load_user(uid):
    return OWNER if uid == 'owner' else None

# Register extension API blueprint
app.register_blueprint(extension_api)

# ── Extension API ─────────────────────────────────────────────────────────────
# Extension API routes are registered via blueprint

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == USERNAME and \
           check_password_hash(PASSWORD_HASH, request.form.get('password','')):
            login_user(OWNER, remember=True)
            return redirect(url_for('dashboard'))
        error = 'Invalid credentials.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    status_filter  = request.args.get('status', 'all')
    keyword_filter = request.args.get('keyword', '')
    company_filter = request.args.get('company', 'all')
    age_filter     = request.args.get('age', 'all')
    settings       = get_settings()
    threshold      = int(settings.get('score_threshold', 6))
    archive_days   = int(settings.get('archive_after_days', 14))

    jobs = get_jobs(status_filter, keyword_filter, company_filter)

    # Attach age badges + filter archived from active view
    from suggestions import get_age_badge, should_archive
    active_jobs   = []
    archived_jobs = []
    for job in jobs:
        badge = get_age_badge(job.get('posted_on') or job.get('found_at'))
        job['age_emoji']  = badge[0]
        job['age_class']  = badge[1]
        job['age_label']  = badge[2]
        if should_archive(job.get('posted_on') or job.get('found_at'), archive_days):
            archived_jobs.append(job)
        else:
            active_jobs.append(job)

    # Age filter
    if age_filter == 'fire':
        active_jobs = [j for j in active_jobs if j['age_class'] == 'age-fire']
    elif age_filter == 'week':
        active_jobs = [j for j in active_jobs if j['age_class'] in ('age-fire','age-fresh')]
    elif age_filter == 'archived':
        active_jobs = archived_jobs

    return render_template('dashboard.html',
        jobs             = active_jobs,
        stats            = get_stats(),
        companies        = get_companies(),
        status_filter    = status_filter,
        keyword_filter   = keyword_filter,
        company_filter   = company_filter,
        age_filter       = age_filter,
        threshold        = threshold,
        archive_days     = archive_days,
    )

# ── Settings ──────────────────────────────────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            save_settings({key: value})
        return jsonify({'ok': True})
    return render_template('settings.html', settings=get_settings())

# ── Profile ───────────────────────────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        data = request.get_json()
        if 'info' in data:
            save_profile_info(data['info'])
        if 'summary' in data:
            save_summary(data['summary'])
        if 'experience' in data:
            save_experience(data['experience'])
        if 'passion' in data:
            save_passion(data['passion'])
        return jsonify({'ok': True})
    return render_template('profile.html', profile=get_profile())

# ── Job Queue Management ──────────────────────────────────────────────────────
@app.route('/queue')
@login_required
def queue():
    threshold = int(get('score_threshold', 6))
    pending_jobs = get_pending_jobs(threshold)
    pending_companies = get_pending_companies()
    return render_template('queue.html',
        pending_jobs=pending_jobs,
        pending_companies=pending_companies
    )

@app.route('/api/approve-job/<int:job_id>', methods=['POST'])
@login_required
def api_approve_job(job_id):
    approve_job(job_id)
    return jsonify({'ok': True})

@app.route('/api/reject-job/<int:job_id>', methods=['POST'])
@login_required
def api_reject_job(job_id):
    reject_job(job_id, request.get_json().get('reason', ''))
    return jsonify({'ok': True})

@app.route('/api/approve-company/<int:company_id>', methods=['POST'])
@login_required
def api_approve_company(company_id):
    add_approved_company(company_id)
    return jsonify({'ok': True})

@app.route('/api/reject-company/<int:company_id>', methods=['POST'])
@login_required
def api_reject_company(company_id):
    reject_company(company_id, request.get_json().get('reason', ''))
    return jsonify({'ok': True})

# ── Companies ─────────────────────────────────────────────────────────────────
@app.route('/companies')
@login_required
def companies():
    active = get_active_companies()
    watching = get_watching_companies()
    rejected = get_auto_rejected_companies()
    stats = get_stats()
    return render_template('companies.html',
        active_companies=active,
        watching_companies=watching,
        rejected_companies=rejected,
        stats=stats
    )

@app.route('/api/restore-company/<int:company_id>', methods=['POST'])
@login_required
def api_restore_company(company_id):
    restore_company(company_id)
    return jsonify({'ok': True})

# ── Async Triggers ───────────────────────────────────────────────────────────
@app.route('/api/trigger-scan', methods=['POST'])
@login_required
def trigger_scan():
    """Manually trigger a company scan."""
    try:
        results = run_scrape(discover=True)
        total_new = sum(r.get('new', 0) for r in results)
        score_pending_jobs()
        return jsonify({'ok': True, 'companies': len(results), 'new_jobs': total_new})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/trigger-score', methods=['POST'])
@login_required
def trigger_score():
    """Manually trigger job scoring."""
    try:
        score_pending_jobs()
        return jsonify({'ok': True, 'message': 'Jobs scored'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/trigger-suggestions', methods=['POST'])
@login_required
def trigger_suggestions():
    """Manually trigger company suggestions."""
    try:
        added = run_suggestion_pipeline()
        return jsonify({'ok': True, 'suggestions_added': added})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ── Extension API ─────────────────────────────────────────────────────────────
@app.route('/api/ping', methods=['GET', 'OPTIONS'])
def api_ping():
    """Health check for Chrome extension."""
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'status': 'ok', 'version': '1.0'})

@app.route('/api/profile', methods=['GET', 'OPTIONS'])
@login_required
def api_profile():
    """Return full profile as JSON for the Chrome extension."""
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify(get_profile())

# ── Cover letter generator ────────────────────────────────────────────────────
@app.route('/api/cover-letter', methods=['POST', 'OPTIONS'])
@login_required
def generate_cover_letter():
    if request.method == 'OPTIONS':
        return '', 204
    
    data        = request.get_json()
    job_desc    = data.get('job_description', '').strip()
    resume_ver  = data.get('resume_version', 'A')

    if not job_desc:
        return jsonify({'ok': False, 'error': 'No job description provided'})

    profile = get_profile()
    info    = profile['info']
    name    = info.get('full_name', 'Khala Wright')
    summary = profile['summaries'].get(resume_ver, '')

    # Get passion statement
    conn = sqlite3.connect(os.path.join(app.root_path, 'jobwatch.db'))
    row  = conn.execute("SELECT passion_statement FROM profile_summary WHERE resume_version='passion'").fetchone()
    conn.close()
    passion = row[0] if row and row[0] else ''

    # Build experience snippet
    exp = profile['experience']
    relevant_exp = [e for e in exp if e['resume_version'] in (resume_ver, 'both')]
    exp_lines = []
    for e in relevant_exp[:2]:
        bullets = e['responsibilities'][:2]
        exp_lines.append(f"{e['job_title']} at {e['company']} ({e['start_date']}–{e['end_date']}): {'; '.join(bullets)}")

    certs  = ', '.join(profile['certifications'])
    skills = profile['skills'].get(resume_ver, {})
    skill_summary = '; '.join(f"{k}: {v}" for k, v in list(skills.items())[:4])

    prompt = f"""Write a 2-paragraph cover letter for this job application. Be specific, direct, and human. No filler phrases like "I am excited to apply" or "I believe I would be a great fit."

CANDIDATE:
Name: {name}
Summary: {summary}
Recent experience: {chr(10).join(exp_lines)}
Certifications: {certs}
Key skills: {skill_summary}
Passion statement (use this as inspiration, do not copy verbatim): {passion[:400]}

JOB DESCRIPTION:
{job_desc[:1500]}

RESUME VERSION: {'Security-focused' if resume_ver == 'A' else 'Engineering/Support-focused'}

INSTRUCTIONS:
- Paragraph 1: Who she is + why she is specifically qualified for THIS role. Reference actual requirements from the job description by name. Show she read it.
- Paragraph 2: What she brings that others won't + one specific project or accomplishment that maps directly to this role. End with a confident close, no begging.
- Tone: Confident, direct, warm. Like someone who knows their worth but isn't arrogant.
- Length: 2 paragraphs, 4-5 sentences each. No salutation, no sign-off — just the body paragraphs.
- Do NOT start with "I" — vary the opening.

Return only the cover letter text, nothing else."""

    from suggestions import call_claude
    result = call_claude(prompt, system='You are a professional cover letter writer. Return only the cover letter body paragraphs, no salutation, no sign-off, no explanation.')

    if not result:
        return jsonify({'ok': False, 'error': 'Claude API unavailable — check ANTHROPIC_API_KEY in .env'})

    return jsonify({'ok': True, 'letter': result.strip()})

# ── Web saves (Send to JobWatch) ──────────────────────────────────────────────
@app.route('/api/save-job', methods=['POST', 'OPTIONS'])
def save_job_from_extension():
    if request.method == 'OPTIONS':
        return '', 204
    
    # Allow unauthenticated saves from extension as long as token matches
    data    = request.get_json()
    token   = data.get('token','')
    ext_tok = os.environ.get('EXTENSION_TOKEN', 'jobwatch-local')
    if token != ext_tok:
        return jsonify({'ok': False, 'error': 'Invalid token'}), 401

    title   = data.get('title','').strip()
    company = data.get('company','').strip()
    url     = data.get('url','').strip()
    desc    = data.get('description','').strip()[:1000]

    if not url:
        return jsonify({'ok': False, 'error': 'No URL provided'})

    is_new = save_web_job(title, company, url, desc)
    if not is_new:
        return jsonify({'ok': True, 'status': 'already_saved', 'message': 'Already in your list'})
    
    count = get_web_saves_count()
    return jsonify({'ok': True, 'status': 'saved', 'pending_count': count})

@app.route('/api/web-saves', methods=['GET', 'OPTIONS'])
@login_required
def get_web_saves_api():
    if request.method == 'OPTIONS':
        return '', 204
    
    from suggestions import get_age_badge, should_archive
    settings     = get_settings()
    archive_days = int(settings.get('archive_after_days', 14))
    
    saves = []
    for job in get_web_saves():
        badge = get_age_badge(job['saved_at'])
        job['age_emoji'] = badge[0]
        job['age_class'] = badge[1]
        job['age_label'] = badge[2]
        job['is_stale']  = should_archive(job['saved_at'], archive_days)
        saves.append(job)
    
    return jsonify(saves)

@app.route('/api/web-saves/<int:save_id>', methods=['POST', 'OPTIONS'])
@login_required
def update_web_save(save_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json()
    status = data.get('status', 'saved')
    update_web_save_status(save_id, status)
    return jsonify({'ok': True})

@app.route('/api/badge-count', methods=['GET', 'OPTIONS'])
def api_badge_count():
    if request.method == 'OPTIONS':
        return '', 204
    
    # Extension can call this without auth to get unseen count
    web_saves = get_web_saves()
    count = len(web_saves) if web_saves else 0
    return jsonify({'count': count})

@app.route('/saved-jobs')
@login_required
def saved_jobs_page():
    from suggestions import get_age_badge, should_archive
    settings     = get_settings()
    archive_days = int(settings.get('archive_after_days', 14))
    
    saves = []
    for r in get_web_saves():
        badge = get_age_badge(r['saved_at'])
        r['age_emoji'] = badge[0]
        r['age_class'] = badge[1]
        r['age_label'] = badge[2]
        r['is_stale']  = should_archive(r['saved_at'], archive_days)
        saves.append(r)
    
    return render_template('saved_jobs.html', saves=saves)

# ── Boot ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    init_queue_tables()
    init_profile_tables()
    init_settings()
    init_approved_companies()
    print('\n  JobWatch → http://localhost:5050\n')
    app.run(debug=False, host='127.0.0.1', port=5050)
