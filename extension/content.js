/**
 * JobWatch Pro - Content Script
 * Detects job application submissions across all job sites
 */

// Configuration
const CONFIG = {
  apiBaseUrl: 'http://localhost:5050', // Change for production
  extensionToken: 'jobwatch-local'
};

// Track submitted forms to avoid duplicates
const submittedForms = new Set();

/**
 * Extract job information from the current page
 */
function extractJobInfo() {
  const jobInfo = {
    url: window.location.href,
    title: extractJobTitle(),
    company: extractCompanyName(),
    timestamp: new Date().toISOString()
  };
  
  return jobInfo;
}

/**
 * Try to extract job title from common selectors
 */
function extractJobTitle() {
  const selectors = [
    'h1[data-testid="job-title"]', // LinkedIn
    'h1.jobsearch-JobInfoHeader-title', // Indeed
    'h1.job-title', // Generic
    '[class*="job-title"]',
    '[class*="position-title"]',
    'h1',
    'title'
  ];
  
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      return element.textContent.trim().substring(0, 200);
    }
  }
  
  return 'Job Application';
}

/**
 * Try to extract company name from common selectors
 */
function extractCompanyName() {
  const selectors = [
    '[data-testid="company-name"]', // LinkedIn
    'h2.jobsearch-InlineCompanyRating-companyHeader', // Indeed
    '[class*="company-name"]',
    '[class*="company"]',
    'a[href*="company"]'
  ];
  
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      return element.textContent.trim().substring(0, 100);
    }
  }
  
  return 'Unknown Company';
}

/**
 * Mark a job as applied in JobWatch backend
 */
async function markJobAsApplied(jobInfo) {
  try {
    const response = await fetch(`${CONFIG.apiBaseUrl}/api/mark-applied`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Extension-Token': CONFIG.extensionToken
      },
      body: JSON.stringify({
        url: jobInfo.url,
        title: jobInfo.title,
        company: jobInfo.company,
        appliedAt: jobInfo.timestamp
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✓ JobWatch: Application tracked', result);
      showNotification('Application tracked in JobWatch!', 'success');
      return true;
    } else {
      console.warn('JobWatch API error:', response.status);
      showNotification('Failed to track application', 'error');
      return false;
    }
  } catch (error) {
    console.error('JobWatch error:', error);
    showNotification('JobWatch connection error', 'error');
    return false;
  }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
  // Send message to background script to show notification
  chrome.runtime.sendMessage({
    action: 'showNotification',
    message: message,
    type: type
  });
}

/**
 * Detect form submissions
 */
function detectFormSubmission() {
  document.addEventListener('submit', (event) => {
    // Check if this looks like a job application form
    const form = event.target;
    const formKey = form.id + form.name + form.action;
    
    // Avoid duplicate submissions
    if (submittedForms.has(formKey)) {
      return;
    }
    
    // Check if form contains typical job application fields
    const hasJobApplicationFields = 
      form.innerHTML.includes('resume') ||
      form.innerHTML.includes('cover letter') ||
      form.innerHTML.includes('application') ||
      form.innerHTML.includes('submit') ||
      form.innerHTML.includes('apply');
    
    if (hasJobApplicationFields) {
      submittedForms.add(formKey);
      
      // Extract job info and mark as applied
      const jobInfo = extractJobInfo();
      markJobAsApplied(jobInfo);
      
      // Log for debugging
      console.log('JobWatch: Application detected', jobInfo);
    }
  }, true);
}

/**
 * Detect navigation changes (for single-page applications like LinkedIn)
 */
function detectNavigationChanges() {
  let lastUrl = location.href;
  
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      // Page changed, reset form tracking
      submittedForms.clear();
    }
  });
  
  observer.observe(document, { subtree: true, childList: true });
}

/**
 * Detect button clicks that might trigger applications
 */
function detectApplicationButtons() {
  document.addEventListener('click', (event) => {
    const target = event.target;
    
    // Check if clicked element is an apply/submit button
    const isApplyButton = 
      target.textContent.toLowerCase().includes('apply') ||
      target.textContent.toLowerCase().includes('submit') ||
      target.textContent.toLowerCase().includes('send') ||
      target.id.toLowerCase().includes('apply') ||
      target.className.toLowerCase().includes('apply');
    
    if (isApplyButton && !target.disabled) {
      // Give the form time to submit, then check if we should track it
      setTimeout(() => {
        const jobInfo = extractJobInfo();
        
        // Only track if URL changed (indicating navigation to confirmation)
        if (location.href !== jobInfo.url) {
          markJobAsApplied(jobInfo);
        }
      }, 1000);
    }
  }, true);
}

/**
 * Listen for messages from popup
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'markCurrentJobAsApplied') {
    const jobInfo = extractJobInfo();
    markJobAsApplied(jobInfo).then(success => {
      sendResponse({ success });
    });
    return true; // Will respond asynchronously
  }
  
  if (request.action === 'getJobInfo') {
    const jobInfo = extractJobInfo();
    sendResponse(jobInfo);
  }
});

/**
 * Initialize content script
 */
function init() {
  console.log('JobWatch Pro: Content script loaded');
  
  // Set up all detection mechanisms
  detectFormSubmission();
  detectNavigationChanges();
  detectApplicationButtons();
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
