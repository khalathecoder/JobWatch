"""
JobWatch Extension API
Handles communication between Chrome extension and Flask backend
"""

from flask import Blueprint, request, jsonify
from database import get_db, update_job_status
import logging

log = logging.getLogger(__name__)

extension_api = Blueprint('extension_api', __name__, url_prefix='/api')

# Extension token for authentication
EXTENSION_TOKEN = None

def set_extension_token(token):
    """Set the extension token from environment"""
    global EXTENSION_TOKEN
    EXTENSION_TOKEN = token

def verify_extension_token():
    """Verify extension token from request header"""
    token = request.headers.get('X-Extension-Token')
    if not token or token != EXTENSION_TOKEN:
        return False
    return True

@extension_api.route('/mark-applied', methods=['POST'])
def mark_applied():
    """
    Mark a job as applied
    
    Request body:
    {
        "url": "https://linkedin.com/jobs/...",
        "title": "Software Engineer",
        "company": "Google",
        "appliedAt": "2024-05-24T12:00:00Z"
    }
    """
    
    # Verify extension token
    if not verify_extension_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url')
        title = data.get('title', 'Unknown Job')
        company = data.get('company', 'Unknown Company')
        applied_at = data.get('appliedAt')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Try to find existing job by URL
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, status FROM jobs WHERE url = ?',
            (url,)
        )
        job = cursor.fetchone()
        
        if job:
            job_id = job[0]
            old_status = job[1]
            
            # Update status to 'applied'
            cursor.execute(
                'UPDATE jobs SET status = ?, applied_at = ? WHERE id = ?',
                ('applied', applied_at, job_id)
            )
            db.commit()
            
            log.info(f'Job {job_id} marked as applied: {title} at {company}')
            
            return jsonify({
                'success': True,
                'message': f'Job marked as applied',
                'job_id': job_id,
                'title': title,
                'company': company,
                'previous_status': old_status,
                'new_status': 'applied'
            }), 200
        else:
            # Job not found in database - create a web save entry instead
            cursor.execute(
                '''INSERT INTO web_saves 
                   (url, title, company, saved_at, status) 
                   VALUES (?, ?, ?, ?, ?)''',
                (url, title, company, applied_at, 'applied')
            )
            db.commit()
            
            log.info(f'Web save created and marked as applied: {title} at {company}')
            
            return jsonify({
                'success': True,
                'message': 'Application tracked (new job)',
                'title': title,
                'company': company,
                'status': 'applied',
                'note': 'Job not found in database, saved as web save'
            }), 200
    
    except Exception as e:
        log.error(f'Error marking job as applied: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@extension_api.route('/save-job', methods=['POST'])
def save_job():
    """
    Save a job from the extension
    
    Request body:
    {
        "url": "https://linkedin.com/jobs/...",
        "title": "Software Engineer",
        "company": "Google",
        "savedAt": "2024-05-24T12:00:00Z"
    }
    """
    
    # Verify extension token
    if not verify_extension_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url')
        title = data.get('title', 'Unknown Job')
        company = data.get('company', 'Unknown Company')
        saved_at = data.get('savedAt')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if already saved
        cursor.execute(
            'SELECT id FROM web_saves WHERE url = ?',
            (url,)
        )
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({
                'success': True,
                'message': 'Job already saved',
                'job_id': existing[0]
            }), 200
        
        # Create new web save
        cursor.execute(
            '''INSERT INTO web_saves 
               (url, title, company, saved_at, status) 
               VALUES (?, ?, ?, ?, ?)''',
            (url, title, company, saved_at, 'saved')
        )
        db.commit()
        
        log.info(f'Job saved from extension: {title} at {company}')
        
        return jsonify({
            'success': True,
            'message': 'Job saved successfully',
            'title': title,
            'company': company,
            'status': 'saved'
        }), 200
    
    except Exception as e:
        log.error(f'Error saving job: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@extension_api.route('/job-info', methods=['GET'])
def get_job_info():
    """
    Get job information by URL
    
    Query params:
    - url: Job URL to look up
    """
    
    # Verify extension token
    if not verify_extension_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        url = request.args.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Try to find in jobs table
        cursor.execute(
            'SELECT id, title, company, status, created_at FROM jobs WHERE url = ?',
            (url,)
        )
        job = cursor.fetchone()
        
        if job:
            return jsonify({
                'found': True,
                'source': 'jobs',
                'id': job[0],
                'title': job[1],
                'company': job[2],
                'status': job[3],
                'created_at': job[4]
            }), 200
        
        # Try to find in web_saves table
        cursor.execute(
            'SELECT id, title, company, status, saved_at FROM web_saves WHERE url = ?',
            (url,)
        )
        save = cursor.fetchone()
        
        if save:
            return jsonify({
                'found': True,
                'source': 'web_saves',
                'id': save[0],
                'title': save[1],
                'company': save[2],
                'status': save[3],
                'saved_at': save[4]
            }), 200
        
        return jsonify({
            'found': False,
            'message': 'Job not found'
        }), 404
    
    except Exception as e:
        log.error(f'Error getting job info: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@extension_api.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint for extension"""
    return jsonify({
        'status': 'ok',
        'message': 'JobWatch extension API is running'
    }), 200
