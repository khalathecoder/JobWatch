/**
 * JobWatch Pro - Popup Script
 * Handles popup UI interactions
 */

const CONFIG = {
  apiBaseUrl: 'http://localhost:5050'
};

// DOM elements
const jobDetailsDiv = document.getElementById('jobDetails');
const markAppliedBtn = document.getElementById('markAppliedBtn');
const openDashboardBtn = document.getElementById('openDashboardBtn');
const statusMessage = document.getElementById('statusMessage');
const settingsLink = document.getElementById('settingsLink');

/**
 * Load and display current job information
 */
async function loadJobInfo() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'getJobInfo' }, (response) => {
      if (response) {
        displayJobInfo(response);
      } else {
        jobDetailsDiv.innerHTML = '<p class="loading">No job information found on this page</p>';
      }
    });
  } catch (error) {
    console.error('Error loading job info:', error);
    jobDetailsDiv.innerHTML = '<p class="loading">Error loading job information</p>';
  }
}

/**
 * Display job information in popup
 */
function displayJobInfo(jobInfo) {
  const html = `
    <div>
      <p><span class="label">Title:</span> <span class="value">${escapeHtml(jobInfo.title)}</span></p>
      <p><span class="label">Company:</span> <span class="value">${escapeHtml(jobInfo.company)}</span></p>
      <p><span class="label">URL:</span> <span class="value" style="font-size: 11px; word-break: break-all;">${escapeHtml(jobInfo.url)}</span></p>
    </div>
  `;
  jobDetailsDiv.innerHTML = html;
}

/**
 * Mark current job as applied
 */
async function markAsApplied() {
  try {
    markAppliedBtn.disabled = true;
    markAppliedBtn.textContent = 'Marking...';
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'markCurrentJobAsApplied' }, (response) => {
      if (response && response.success) {
        showStatus('✓ Application tracked in JobWatch!', 'success');
        markAppliedBtn.textContent = '✓ Marked as Applied';
      } else {
        showStatus('✗ Failed to track application', 'error');
        markAppliedBtn.disabled = false;
        markAppliedBtn.textContent = '✓ Mark as Applied';
      }
    });
  } catch (error) {
    console.error('Error marking as applied:', error);
    showStatus('✗ Error: ' + error.message, 'error');
    markAppliedBtn.disabled = false;
    markAppliedBtn.textContent = '✓ Mark as Applied';
  }
}

/**
 * Open JobWatch dashboard
 */
function openDashboard() {
  chrome.tabs.create({ url: CONFIG.apiBaseUrl });
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.className = `status-message show ${type}`;
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    statusMessage.classList.remove('show');
  }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Initialize popup
 */
function init() {
  // Load job info when popup opens
  loadJobInfo();
  
  // Set up event listeners
  markAppliedBtn.addEventListener('click', markAsApplied);
  openDashboardBtn.addEventListener('click', openDashboard);
  settingsLink.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
