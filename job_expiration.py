"""
Job Expiration Checker
Validates job URLs to detect when postings are no longer available.
Automatically marks expired jobs as 'closed' in the database.
"""
import requests
import logging
from datetime import datetime
from database import get_conn, mark_expired, log_scan

logger = logging.getLogger(__name__)

# Timeout for URL requests (seconds)
REQUEST_TIMEOUT = 10

# HTTP status codes that indicate a job is still valid
VALID_STATUS_CODES = {200, 301, 302, 303, 307, 308}

# Status codes that indicate a job has been removed
EXPIRED_STATUS_CODES = {404, 410}

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def check_url_valid(url: str) -> bool:
    """
    Check if a job URL is still valid (returns 200-308 status).
    Returns True if URL is reachable, False if expired or unreachable.
    """
    if not url or not url.startswith('http'):
        return False
    
    try:
        response = requests.head(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        # If we get a 404 or 410, the job is definitely expired
        if response.status_code in EXPIRED_STATUS_CODES:
            logger.info(f"Job expired (HTTP {response.status_code}): {url}")
            return False
        
        # If we get a valid status code, the job is still there
        if response.status_code in VALID_STATUS_CODES:
            logger.debug(f"Job valid (HTTP {response.status_code}): {url}")
            return True
        
        # For other status codes, try GET as fallback
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code in EXPIRED_STATUS_CODES:
            logger.info(f"Job expired (HTTP {response.status_code} on GET): {url}")
            return False
        
        # If we got content, assume it's still valid
        return response.status_code < 400
        
    except requests.exceptions.Timeout:
        logger.warning(f"URL timeout (may be temporary): {url}")
        return True  # Assume valid if timeout (might be server issue)
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error (may be temporary): {url}")
        return True  # Assume valid if connection error
    except Exception as e:
        logger.warning(f"Error checking URL {url}: {e}")
        return True  # Assume valid on unknown error (don't mark as expired)

def check_job_expiration(job_id: int, url: str) -> bool:
    """
    Check if a specific job has expired and mark it in the database if so.
    Returns True if job is still valid, False if expired.
    """
    if not check_url_valid(url):
        mark_expired(job_id)
        return False
    return True

def check_all_jobs_expiration(batch_size: int = 50) -> dict:
    """
    Check expiration status for all active jobs in the database.
    Returns stats on how many jobs were checked and marked as expired.
    
    Args:
        batch_size: Process jobs in batches to avoid overwhelming the server
    
    Returns:
        dict with keys: 'total_checked', 'expired_count', 'valid_count', 'errors'
    """
    conn = get_conn()
    
    # Get all non-expired jobs
    jobs = conn.execute(
        "SELECT id, url, company, title FROM jobs WHERE expired=0 ORDER BY found_at DESC"
    ).fetchall()
    conn.close()
    
    stats = {
        'total_checked': len(jobs),
        'expired_count': 0,
        'valid_count': 0,
        'errors': []
    }
    
    logger.info(f"Starting expiration check for {len(jobs)} jobs")
    
    for i, job in enumerate(jobs):
        try:
            job_id = job['id']
            url = job['url']
            company = job['company']
            title = job['title']
            
            if not check_url_valid(url):
                mark_expired(job_id)
                stats['expired_count'] += 1
                logger.info(f"Marked expired: {company} - {title}")
            else:
                stats['valid_count'] += 1
            
            # Log progress every 10 jobs
            if (i + 1) % 10 == 0:
                logger.debug(f"Checked {i + 1}/{len(jobs)} jobs")
                
        except Exception as e:
            error_msg = f"Error checking job {job['id']}: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
    
    logger.info(f"Expiration check complete: {stats['expired_count']} expired, {stats['valid_count']} valid")
    return stats

def cleanup_old_expired_jobs(days: int = 30) -> int:
    """
    Remove jobs that have been marked as expired for more than N days.
    This keeps the database clean while preserving recent history.
    
    Args:
        days: Number of days to keep expired jobs before deletion
    
    Returns:
        Number of jobs deleted
    """
    conn = get_conn()
    
    # Delete expired jobs older than N days
    cursor = conn.execute(
        "DELETE FROM jobs WHERE expired=1 AND datetime(found_at) < datetime('now', ?)",
        (f'-{days} days',)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired jobs older than {days} days")
    
    return deleted_count

if __name__ == '__main__':
    # Test the expiration checker
    logging.basicConfig(level=logging.INFO)
    
    # Example: Check a specific URL
    test_url = "https://www.google.com"
    print(f"Testing URL: {test_url}")
    print(f"Valid: {check_url_valid(test_url)}")
    
    # Example: Check all jobs
    # stats = check_all_jobs_expiration()
    # print(f"Stats: {stats}")
