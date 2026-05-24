/**
 * JobWatch Pro - Background Service Worker
 * Handles notifications and background tasks
 */

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showNotification') {
    showNotification(request.message, request.type, sender.tab.id);
  }
});

/**
 * Show notification to user
 */
function showNotification(message, type = 'info', tabId = null) {
  const iconMap = {
    success: 'icons/icon-48.png',
    error: 'icons/icon-48.png',
    info: 'icons/icon-48.png'
  };
  
  const titleMap = {
    success: '✓ JobWatch',
    error: '✗ JobWatch',
    info: 'ℹ JobWatch'
  };
  
  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL(iconMap[type]),
    title: titleMap[type],
    message: message,
    priority: 2
  });
}

/**
 * Handle extension icon click
 */
chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      // Send message to content script to get job info
      chrome.runtime.sendMessage({ action: 'getJobInfo' }, (response) => {
        console.log('Current job:', response);
      });
    }
  });
});

/**
 * Initialize background worker
 */
console.log('JobWatch Pro: Background service worker loaded');
