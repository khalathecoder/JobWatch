"""
JobWatch — Flask application
Single-user dashboard: auth, job queue review, company management, settings.
"""
import os, threading, json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from database import (
    init_db, get_jobs, update_status, mark_seen, get_companies, get_stats,
    get_pending_jobs, get_pending_companies, get_queue_counts,
    approve_job, reject_job, approve_company, reject_company,
    add_approved_company, get_active_companies, get_watching_companies,
    get_auto_rejected_companies, get_company_stats, restore_company,
    update_last_scanned,
)
from scraper import run_scrape, get_company_names, run_company_scan
from suggestions import score_pending_jobs, log_preference, get_age_badge
from settings_db import init_settings, get_all as get_settings, save_all as save_settings, get as get_setting

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-change-this')

# ── Auth ──────────────────────────────────────────────────────────────────────
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if (request.form.get('username') == USERNAME and
                check_password_hash(PASSWORD_HASH, request.form.get('password', ''))):
            login_user(OWNER, remember=True)
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html', error=None)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    settings     = get_settings()
    threshold    = int(settings.get('score_threshold', 6))

    status_filter  = request.args.get('status', 'all')
    keyword_filter = request.args.get('keyword', '')
    company_filter = request.args.get('company', 'all')
    age_filter     = request.args.get('age', 'all')

    jobs = get_jobs(
        status_filter  if status_filter  != 'all' else None,
        keyword_filter or None,
        company_filter if company_filter != 'all' else None,
    )

    # Attach age badges
    for job in jobs:
        badge = get_age_badge(job.get('posted_on') or job.get('found_at'))
        job['age_emoji'] = badge[0]
        job['age_class'] = badge[1]
        job['age_label'] = badge[2]

    # Age filter
    if age_filter == 'fire':
        jobs = [j for j in jobs if j['age_class'] == 'age-fire']
    elif age_filter == 'week':
        jobs = [j for j in jobs if j['age_class'] in ('age-fire', 'age-fresh')]

    return render_template('dashboard.html',
        jobs              = jobs,
        stats             = get_stats(),
        companies         = get_companies(),
        all_targets       = get_company_names(),
        pending_jobs      = get_pending_jobs(threshold),
        pending_companies = get_pending_companies(),
        queue_counts      = get_queue_counts(),
        filters           = {
            'status': status_filter, 'keyword': keyword_filter,
            'company': company_filter, 'age': age_filter,
        },
        settings          = settings,
    )


# ── Queue decisions ───────────────────────────────────────────────────────────
@app.route('/api/queue/job', methods=['POST'])
@login_required
def queue_job_decision():
    data     = request.get_json()
    jid      = data.get('id')
    decision = data.get('decision')
    if decision == 'approve':
        job = approve_job(jid)
        if job:
            log_preference('job', f"{job['title']} @ {job['company']}",
                           'approved', job.get('keywords', ''), '', '')
    else:
        job = reject_job(jid, data.get('reason', ''))
        if job:
            log_preference('job', f"{job['title']} @ {job['company']}",
                           'rejected', job.get('keywords', ''), '', '')
    return jsonify({'ok': True})


@app.route('/api/queue/company', methods=['POST'])
@login_required
def queue_company_decision():
    data     = request.get_json()
    cid      = data.get('id')
    decision = data.get('decision')
    if decision == 'approve':
        co = add_approved_company(cid)
        if co:
            log_preference('company', co['name'], 'approved',
                           co.get('sector', ''), co.get('sector', ''),
                           co.get('why_suggested', ''))
            # Immediately scan in background
            def _scan(name):
                run_scrape(name)
                score_pending_jobs()
                update_last_scanned(name)
            threading.Thread(target=_scan, args=(co['name'],), daemon=True).start()
    else:
        reject_company(cid, data.get('reason', ''))
    return jsonify({'ok': True})


# ── Job status ────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['POST'])
@login_required
def set_status():
    data = request.get_json()
    if data.get('id') and data.get('status') in ('new', 'saved', 'applied', 'rejected'):
        update_status(data['id'], data['status'])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


@app.route('/api/seen', methods=['POST'])
@login_required
def set_seen():
    mark_seen(request.get_json().get('id'))
    return jsonify({'ok': True})


# ── Scan / score ──────────────────────────────────────────────────────────────
@app.route('/api/scan', methods=['POST'])
@login_required
def trigger_scan():
    company = (request.get_json() or {}).get('company')
    def _run():
        run_scrape(company)
        score_pending_jobs()
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'ok': True})


@app.route('/api/score', methods=['POST'])
@login_required
def trigger_scoring():
    threading.Thread(target=score_pending_jobs, daemon=True).start()
    return jsonify({'ok': True})


@app.route('/api/scan/company/<int:company_id>', methods=['POST'])
@login_required
def scan_company(company_id):
    threading.Thread(target=run_company_scan, args=(company_id,), daemon=True).start()
    return jsonify({'ok': True})


# ── Company suggestions pipeline ──────────────────────────────────────────────
@app.route('/api/suggest', methods=['POST'])
@login_required
def trigger_suggestions():
    from company_pipeline import run_suggestion_pipeline
    threading.Thread(target=run_suggestion_pipeline, daemon=True).start()
    return jsonify({'ok': True, 'message': 'Generating company suggestions...'})


# ── Companies page ────────────────────────────────────────────────────────────
@app.route('/companies')
@login_required
def companies():
    return render_template('companies.html',
        active_companies   = get_active_companies(),
        watching_companies = get_watching_companies(),
        rejected_companies = get_auto_rejected_companies(),
        stats              = get_company_stats(),
        grace_days         = int(get_setting('company_grace_days') or 14),
    )


@app.route('/api/company/restore', methods=['POST'])
@login_required
def restore_company_route():
    restore_company(request.get_json().get('id'))
    return jsonify({'ok': True})


# ── Settings page ─────────────────────────────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    saved = False
    if request.method == 'POST':
        data = {}
        for field in ['archive_after_days', 'score_threshold',
                      'suggestion_interval', 'sectors', 'company_grace_days']:
            data[field] = request.form.get(field, '')
        data['must_match'] = ','.join(
            l.strip() for l in request.form.get('must_match', '').splitlines() if l.strip())
        data['exclude'] = ','.join(
            l.strip() for l in request.form.get('exclude', '').splitlines() if l.strip())
        save_settings(data)
        saved = True
    return render_template('settings.html',
        settings    = get_settings(),
        saved       = saved,
        api_key_set = bool(os.environ.get('ANTHROPIC_API_KEY')),
    )


# ── Boot ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    init_settings()
    print('\n  JobWatch running at  http://localhost:5000\n')
    app.run(debug=False, host='127.0.0.1', port=5000)
