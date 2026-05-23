import os, threading, json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import (init_db, init_queue_tables, get_jobs, update_status, mark_seen,
                      get_companies, get_stats, get_pending_companies, get_pending_jobs,
                      get_queue_counts, approve_company, reject_company, approve_job, reject_job,
                      get_active_companies, get_watching_companies, get_auto_rejected_companies,
                      restore_company, get_company_stats)
from scraper import run_scrape, get_company_names, run_company_scan
from profile_db import init_profile_tables, get_profile, save_profile_info, save_summary, save_experience, save_passion
from settings_db import init_settings, get_all as get_settings, save_all as save_settings, get
from suggestions import score_pending_jobs, log_preference
from company_pipeline import run_suggestion_pipeline

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

class User(UserMixin):
    id = 'owner'
OWNER = User()

@login_manager.user_loader
def load_user(uid):
    return OWNER if uid == 'owner' else None

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
        all_targets      = get_company_names(),
        resumes          = get_resume_list(),
        profile          = get_profile(),
        pending_companies= get_pending_companies(),
        pending_jobs     = get_pending_jobs(threshold),
        queue_counts     = get_queue_counts(),
        filters          = {'status': status_filter, 'keyword': keyword_filter,
                            'company': company_filter, 'age': age_filter},
        settings         = settings
    )

# ── Settings ──────────────────────────────────────────────────────────────────
@app.route('/settings', methods=['GET','POST'])
@login_required
def settings_page():
    saved = False
    if request.method == 'POST':
        data = {}
        for field in ['archive_after_days','score_threshold','suggestion_interval','sectors','company_grace_days']:
            data[field] = request.form.get(field, '')
        # Convert textarea newlines back to comma lists
        data['must_match'] = ','.join(
            l.strip() for l in request.form.get('must_match','').splitlines() if l.strip())
        data['exclude'] = ','.join(
            l.strip() for l in request.form.get('exclude','').splitlines() if l.strip())
        save_settings(data)
        saved = True
    return render_template('settings.html',
        settings    = get_settings(),
        saved       = saved,
        api_key_set = bool(os.environ.get('ANTHROPIC_API_KEY'))
    )

# ── Profile ───────────────────────────────────────────────────────────────────
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    saved = False
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'info':
            save_profile_info({f: request.form.get(f,'') for f in
                ['full_name','email','phone','location','linkedin','github','website']})
            saved = True
        elif action == 'summary':
            save_summary('A', request.form.get('summary_a',''))
            save_summary('B', request.form.get('summary_b',''))
            save_passion(request.form.get('passion_statement',''))
            saved = True
        elif action == 'experience':
            exp_id = int(request.form.get('exp_id'))
            bullets = [b.strip() for b in request.form.get('responsibilities','').split('\n') if b.strip()]
            save_experience(exp_id, {
                'job_title': request.form.get('job_title',''),
                'company': request.form.get('company',''),
                'start_date': request.form.get('start_date',''),
                'end_date': request.form.get('end_date',''),
                'resume_version': request.form.get('resume_version','both'),
                'responsibilities': bullets,
            })
            saved = True
    return render_template('profile.html', profile=get_profile(), saved=saved)

# ── Job actions ───────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['POST'])
@login_required
def set_status():
    data = request.get_json()
    if data.get('id') and data.get('status') in ('new','saved','applied','rejected'):
        update_status(data['id'], data['status'])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400

@app.route('/api/seen', methods=['POST'])
@login_required
def set_seen():
    mark_seen(request.get_json().get('id'))
    return jsonify({'ok': True})

@app.route('/api/scan', methods=['POST'])
@login_required
def trigger_scan():
    company = request.get_json().get('company')
    def run():
        run_scrape(company)
        score_pending_jobs()  # score newly queued jobs after scrape
    threading.Thread(target=run, daemon=True).start()
    return jsonify({'ok': True})

# ── Queue decisions ───────────────────────────────────────────────────────────
@app.route('/api/queue/company', methods=['POST'])
@login_required
def queue_company():
    data     = request.get_json()
    cid      = data.get('id')
    decision = data.get('decision')
    if decision == 'approve':
        co = add_approved_company(cid)   # adds to approved_companies + marks suggestion approved
        if co:
            log_preference('company', co['name'], 'approved',
                           co.get('sector',''), co.get('sector',''), co.get('why_suggested',''))
            # Scan this company immediately in background
            def scan_new(name):
                run_scrape(name)
                score_pending_jobs()
                update_last_scanned(name)
            threading.Thread(target=scan_new, args=(co['name'],), daemon=True).start()
    else:
        co = reject_company(cid)
        if co:
            log_preference('company', co['name'], 'rejected',
                           co.get('sector',''), co.get('sector',''), '')
    return jsonify({'ok': True, 'scanning': decision == 'approve'})

@app.route('/api/queue/job', methods=['POST'])
@login_required
def queue_job_decision():
    data     = request.get_json()
    jid      = data.get('id')
    decision = data.get('decision')
    if decision == 'approve':
        job = approve_job(jid)
        if job:
            log_preference('job', f"{job['title']} @ {job['company']}", 'approved',
                           job.get('keywords',''), '', job.get('score_reason',''))
    else:
        job = reject_job(jid)
        if job:
            log_preference('job', f"{job['title']} @ {job['company']}", 'rejected',
                           job.get('keywords',''), '', job.get('score_reason',''))
    return jsonify({'ok': True})

@app.route('/api/suggest', methods=['POST'])
@login_required
def trigger_suggestions():
    threading.Thread(target=run_suggestion_pipeline, daemon=True).start()
    return jsonify({'ok': True, 'message': 'Generating company suggestions...'})

@app.route('/api/score', methods=['POST'])
@login_required
def trigger_scoring():
    threading.Thread(target=score_pending_jobs, daemon=True).start()
    return jsonify({'ok': True, 'message': 'Scoring queued jobs...'})


# ── Companies tab ─────────────────────────────────────────────────────────────
@app.route('/companies')
@login_required
def companies():
    from datetime import datetime
    from settings_db import get_grace_days
    grace = get_grace_days()
    def days_since(dt_str):
        if not dt_str: return 0
        try:
            return (datetime.now() - datetime.fromisoformat(dt_str)).days
        except: return 0
    return render_template('companies.html',
        active_companies   = get_active_companies(),
        watching_companies = get_watching_companies(),
        rejected_companies = get_auto_rejected_companies(),
        stats              = get_company_stats(),
        grace_days         = grace,
        now                = datetime.now().isoformat()
    )

@app.route('/api/scan/company/<int:company_id>', methods=['POST'])
@login_required
def scan_single_company(company_id):
    threading.Thread(target=run_company_scan, args=(company_id,), daemon=True).start()
    return jsonify({'ok': True})

@app.route('/api/company/restore', methods=['POST'])
@login_required
def restore_company_route():
    company_id = request.get_json().get('id')
    restore_company(company_id)
    return jsonify({'ok': True})

# ── Resumes ───────────────────────────────────────────────────────────────────
@app.route('/resumes/<filename>')
@login_required
def serve_resume(filename):
    return send_from_directory(os.path.join(app.root_path, 'resumes'), filename, as_attachment=True)

def get_resume_list():
    d = os.path.join(app.root_path, 'resumes')
    if not os.path.exists(d): return []
    files = []
    for f in os.listdir(d):
        if f.endswith(('.docx','.pdf')):
            label = f.replace('_',' ').replace('.docx','').replace('.pdf','')
            tag   = 'Security' if 'Security' in f else 'Support / Dev' if 'v2' in f else 'General'
            files.append({'filename': f, 'label': label, 'tag': tag})
    return files


# ── Extension API endpoints ───────────────────────────────────────────────────
def add_cors_headers(response):
    """Allow Chrome extension to call Flask APIs."""
    response.headers['Access-Control-Allow-Origin']      = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers']     = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods']     = 'GET, POST, OPTIONS'
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

@app.route('/api/ping')
def ping():
    """Health check for extension."""
    return jsonify({'ok': True, 'version': '1.0'})

@app.route('/api/profile')
@login_required
def api_profile():
    """Return full profile as JSON for the Chrome extension."""
    return jsonify(get_profile())

# ── Boot ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    init_queue_tables()
    init_profile_tables()
    init_settings()
    init_approved_companies()
    print('\n  JobWatch → http://localhost:5050\n')
    app.run(debug=False, host='127.0.0.1', port=5050)

# ── Cover letter generator ────────────────────────────────────────────────────
@app.route('/api/cover-letter', methods=['POST'])
@login_required
def generate_cover_letter():
    import sqlite3
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
    import sqlite3
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

    db = os.path.join(app.root_path, 'jobwatch.db')
    conn = sqlite3.connect(db)
    existing = conn.execute('SELECT id FROM web_saves WHERE url=?', (url,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': True, 'status': 'already_saved', 'message': 'Already in your list'})
    conn.execute(
        'INSERT INTO web_saves (title, company, url, description) VALUES (?,?,?,?)',
        (title, company, url, desc)
    )
    conn.commit()
    # Get total unseen count for badge
    count = conn.execute("SELECT COUNT(*) FROM web_saves WHERE status='saved'").fetchone()[0]
    conn.close()
    return jsonify({'ok': True, 'status': 'saved', 'pending_count': count})

@app.route('/api/web-saves')
@login_required
def get_web_saves():
    import sqlite3
    db   = os.path.join(app.root_path, 'jobwatch.db')
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM web_saves ORDER BY saved_at DESC"
    ).fetchall()
    conn.close()
    from suggestions import get_age_badge, should_archive
    saves = []
    settings = get_settings()
    archive_days = int(settings.get('archive_after_days', 14))
    for r in rows:
        job = dict(r)
        badge = get_age_badge(job['saved_at'])
        job['age_emoji']  = badge[0]
        job['age_class']  = badge[1]
        job['age_label']  = badge[2]
        job['is_stale']   = should_archive(job['saved_at'], archive_days)
        saves.append(job)
    return jsonify(saves)

@app.route('/api/web-saves/<int:save_id>', methods=['POST'])
@login_required
def update_web_save(save_id):
    import sqlite3
    status = request.get_json().get('status')
    if status not in ('saved', 'applied', 'rejected', 'archived'):
        return jsonify({'ok': False}), 400
    db = os.path.join(app.root_path, 'jobwatch.db')
    conn = sqlite3.connect(db)
    conn.execute('UPDATE web_saves SET status=? WHERE id=?', (status, save_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/badge-count')
def badge_count():
    """Returns pending count for extension badge — no auth needed."""
    import sqlite3
    db   = os.path.join(app.root_path, 'jobwatch.db')
    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM web_saves WHERE status='saved'").fetchone()[0]
    conn.close()
    return jsonify({'count': count})

@app.route('/saved-jobs')
@login_required
def saved_jobs_page():
    import sqlite3
    from suggestions import get_age_badge, should_archive
    db   = os.path.join(app.root_path, 'jobwatch.db')
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM web_saves ORDER BY saved_at DESC").fetchall()
    conn.close()
    settings     = get_settings()
    archive_days = int(settings.get('archive_after_days', 14))
    saves = []
    for r in rows:
        job = dict(r)
        badge = get_age_badge(job['saved_at'])
        job['age_emoji'] = badge[0]
        job['age_class'] = badge[1]
        job['age_label'] = badge[2]
        job['is_stale']  = should_archive(job['saved_at'], archive_days)
        saves.append(job)
    return render_template('saved_jobs.html', saves=saves)
