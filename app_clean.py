"""
Clean Flask app for JobWatch.
Uses unified db_schema module for all database operations.
"""
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import os
import json

# Import unified database module
from db_schema import (
    init_db, get_conn,
    add_job, get_jobs, update_job_status, update_job_score, mark_job_applied,
    add_approved_company, get_approved_companies, suggest_company, get_company_suggestions, approve_company_suggestion,
    save_profile_info, get_profile_info, save_summary, save_passion_statement, get_profile_summary,
    add_notification, mark_notification_sent, get_unsent_notifications
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
CORS(app)

# Initialize database on startup
with app.app_context():
    init_db()

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard."""
    jobs = get_jobs()
    stats = {
        'total': len(jobs),
        'new': len([j for j in jobs if j['status'] == 'new']),
        'applied': len([j for j in jobs if j['status'] == 'applied']),
        'rejected': len([j for j in jobs if j['status'] == 'rejected']),
        'avg_score': sum([j['score'] for j in jobs]) // len(jobs) if jobs else 0
    }
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@app.route('/jobs')
def jobs_page():
    """Jobs page."""
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    company = request.args.get('company')
    jobs = get_jobs(status, keyword, company)
    return render_template('jobs.html', jobs=jobs)

@app.route('/companies')
def companies_page():
    """Companies management page."""
    approved = get_approved_companies()
    suggestions = get_company_suggestions('pending')
    return render_template('companies.html', approved=approved, suggestions=suggestions)

@app.route('/profile')
def profile_page():
    """Profile page."""
    profile_info = get_profile_info()
    profile_summary = get_profile_summary()
    return render_template('profile.html', info=profile_info, summary=profile_summary)

# ============================================================================
# API ROUTES - JOBS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def api_get_jobs():
    """Get jobs via API."""
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    company = request.args.get('company')
    jobs = get_jobs(status, keyword, company)
    return jsonify(jobs)

@app.route('/api/jobs', methods=['POST'])
def api_add_job():
    """Add a new job."""
    data = request.json
    success = add_job(
        data['company'],
        data['title'],
        data['url'],
        data.get('description', ''),
        data.get('posted_date', ''),
        data.get('source', 'manual')
    )
    return jsonify({'success': success}), 201 if success else 409

@app.route('/api/jobs/<int:job_id>/status', methods=['PUT'])
def api_update_job_status(job_id):
    """Update job status."""
    data = request.json
    update_job_status(job_id, data['status'])
    return jsonify({'success': True})

@app.route('/api/jobs/<int:job_id>/score', methods=['PUT'])
def api_update_job_score(job_id):
    """Update job score."""
    data = request.json
    update_job_score(job_id, data['score'], data.get('match_reason', ''))
    return jsonify({'success': True})

@app.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
def api_mark_applied(job_id):
    """Mark job as applied."""
    mark_job_applied(job_id)
    return jsonify({'success': True})

# ============================================================================
# API ROUTES - COMPANIES
# ============================================================================

@app.route('/api/companies', methods=['GET'])
def api_get_companies():
    """Get approved companies."""
    companies = get_approved_companies()
    return jsonify(companies)

@app.route('/api/companies', methods=['POST'])
def api_add_company():
    """Add a company."""
    data = request.json
    success = add_approved_company(
        data['name'],
        data.get('sector', ''),
        data.get('ats_type', 'Unknown'),
        data.get('workday_tenant', ''),
        data.get('careers_url', ''),
        data.get('hq', ''),
        data.get('why_added', '')
    )
    return jsonify({'success': success}), 201 if success else 409

@app.route('/api/companies/suggestions', methods=['GET'])
def api_get_suggestions():
    """Get company suggestions."""
    status = request.args.get('status', 'pending')
    suggestions = get_company_suggestions(status)
    return jsonify(suggestions)

@app.route('/api/companies/suggestions', methods=['POST'])
def api_suggest_company():
    """Suggest a company."""
    data = request.json
    success = suggest_company(
        data['name'],
        data.get('sector', ''),
        data.get('ats_type', 'Unknown'),
        data.get('hq', ''),
        data.get('careers_url', ''),
        data.get('why_suggested', ''),
        json.dumps(data.get('sample_roles', []))
    )
    return jsonify({'success': success}), 201 if success else 409

@app.route('/api/companies/suggestions/<int:suggestion_id>/approve', methods=['POST'])
def api_approve_suggestion(suggestion_id):
    """Approve a company suggestion."""
    approve_company_suggestion(suggestion_id)
    return jsonify({'success': True})

# ============================================================================
# API ROUTES - PROFILE
# ============================================================================

@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    """Get profile info."""
    info = get_profile_info()
    summary = get_profile_summary()
    return jsonify({'info': info, 'summary': summary})

@app.route('/api/profile', methods=['PUT'])
def api_update_profile():
    """Update profile info."""
    data = request.json
    save_profile_info(data)
    return jsonify({'success': True})

@app.route('/api/profile/summary', methods=['POST'])
def api_save_summary():
    """Save profile summary."""
    data = request.json
    save_summary(data['version'], data['text'])
    return jsonify({'success': True})

@app.route('/api/profile/passion', methods=['POST'])
def api_save_passion():
    """Save passion statement."""
    data = request.json
    save_passion_statement(data['text'])
    return jsonify({'success': True})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
