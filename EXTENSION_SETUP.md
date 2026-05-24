# JobWatch Pro Chrome Extension Setup

The JobWatch Pro Chrome extension automatically detects when you submit job applications and marks them as "applied" in your JobWatch dashboard.

## Features

✅ **Automatic Application Detection**
- Monitors form submissions across all job sites
- Detects LinkedIn, Indeed, company career pages, Greenhouse, Workday, Lever, etc.
- Works on any website with a job application form

✅ **One-Click Manual Marking**
- "Mark as Applied" button in extension popup
- Manually track applications if automatic detection doesn't work

✅ **Quick Dashboard Access**
- "Open Dashboard" button to access JobWatch
- View all your tracked jobs

✅ **Real-Time Notifications**
- Get confirmation when applications are tracked
- See job details in extension popup

## Installation

### Step 1: Prepare the Extension

The extension files are located in `/home/ubuntu/JobWatch/extension/`:

```
extension/
├── manifest.json      # Extension configuration
├── content.js         # Application detection logic
├── background.js      # Background service worker
├── popup.html         # Popup UI
├── popup.js           # Popup interactions
├── popup.css          # Popup styling
└── icons/             # Extension icons (optional)
```

### Step 2: Load Extension in Chrome

1. Open Chrome and go to: `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Navigate to `/home/ubuntu/JobWatch/extension/` folder
5. Click "Select Folder"

The extension should now appear in your extensions list with a purple icon.

### Step 3: Configure Extension

The extension needs to know where your JobWatch backend is running:

**For Local Development:**
- Extension is pre-configured for `http://localhost:5050`
- No additional setup needed

**For Cloud Deployment:**
1. Edit `extension/content.js` line 8:
   ```javascript
   const CONFIG = {
     apiBaseUrl: 'https://your-app.railway.app', // Change this
     extensionToken: 'jobwatch-local'
   };
   ```

2. Edit `extension/popup.js` line 6:
   ```javascript
   const CONFIG = {
     apiBaseUrl: 'https://your-app.railway.app' // Change this
   };
   ```

3. Reload the extension in Chrome (click reload icon on extensions page)

## Usage

### Automatic Application Detection

1. **Navigate to a job posting** (LinkedIn, Indeed, company site, etc.)
2. **Fill out the application form** as usual
3. **Submit the form** - the extension automatically detects this
4. **See confirmation** - extension shows "Application tracked in JobWatch!"
5. **Check dashboard** - job is marked as "applied"

### Manual Marking

If automatic detection doesn't work:

1. **Click the JobWatch extension icon** (purple icon in toolbar)
2. **Review the job details** shown in the popup
3. **Click "Mark as Applied"** button
4. **See confirmation** - job is marked as applied

### View Dashboard

1. **Click the JobWatch extension icon**
2. **Click "Open Dashboard"** button
3. **View all your tracked jobs**

## How It Works

### Automatic Detection

The extension monitors:
- **Form submissions** - Detects when you submit an application
- **Button clicks** - Detects when you click "Apply" or "Submit"
- **Page navigation** - Tracks when you're redirected to confirmation page

When a submission is detected:
1. Extension extracts job title and company from the page
2. Sends data to JobWatch backend with your extension token
3. Backend finds matching job in database
4. Job status is updated to "applied"
5. You get a confirmation notification

### Manual Marking

When you click "Mark as Applied":
1. Extension gets current page URL, job title, and company
2. Sends to JobWatch backend
3. Backend updates job status
4. Confirmation is shown

## Troubleshooting

### Extension not detecting applications

**Check 1: Is the extension enabled?**
- Go to `chrome://extensions/`
- Make sure JobWatch Pro is enabled (toggle is on)

**Check 2: Is the backend running?**
- Start Flask app: `python app.py`
- Check it's accessible at `http://localhost:5050`

**Check 3: Is the token correct?**
- Check `.env` file has `EXTENSION_TOKEN=jobwatch-local`
- Reload extension in Chrome

**Check 4: Check browser console**
- Right-click on page → Inspect
- Go to Console tab
- Look for JobWatch messages
- Report any errors

### "Failed to track application" error

**Possible causes:**
1. Flask app is not running
2. Backend URL is wrong (check CONFIG in content.js)
3. Extension token doesn't match (check .env)
4. Job not found in database (it will be saved as web save)

**Solution:**
1. Verify Flask app is running: `python app.py`
2. Check backend is accessible: `curl http://localhost:5050/api/ping`
3. Check extension token matches `.env`
4. Try manual marking instead

### Extension popup shows "No job information"

This happens on pages without job postings (e.g., Google homepage).

**Solution:**
- Navigate to an actual job posting page
- Reload the extension popup
- Job details should now appear

### Job not appearing in dashboard

**Possible causes:**
1. Job was saved as "web save" (not in main jobs table)
2. Job URL doesn't match exactly
3. Dashboard needs refresh

**Solution:**
1. Go to dashboard and refresh (F5)
2. Check "Web Saves" section for the job
3. Manually mark as applied from popup

## Advanced Configuration

### Change Extension Token

To use a different token (for security):

1. Edit `.env`:
   ```
   EXTENSION_TOKEN=your-custom-token-here
   ```

2. Edit `extension/content.js` line 9:
   ```javascript
   extensionToken: 'your-custom-token-here'
   ```

3. Reload extension in Chrome

### Disable Automatic Detection

If automatic detection is too aggressive:

1. Edit `extension/content.js`
2. Comment out these lines (around line 100):
   ```javascript
   // detectFormSubmission();
   // detectApplicationButtons();
   ```
3. Reload extension

Now only manual marking will work.

### Add Custom Icons

To customize the extension icon:

1. Create icon files:
   - `extension/icons/icon-16.png` (16x16 pixels)
   - `extension/icons/icon-48.png` (48x48 pixels)
   - `extension/icons/icon-128.png` (128x128 pixels)

2. Reload extension in Chrome

## Publishing to Chrome Web Store

To publish the extension publicly:

1. **Create a Google Developer account** at https://chrome.google.com/webstore/developer/dashboard
2. **Pay $5 registration fee**
3. **Prepare extension package**:
   ```bash
   cd /home/ubuntu/JobWatch/extension
   zip -r jobwatch-pro.zip .
   ```
4. **Upload to Chrome Web Store**:
   - Go to developer dashboard
   - Click "New item"
   - Upload `jobwatch-pro.zip`
   - Fill in details (description, screenshots, etc.)
   - Submit for review

5. **Wait for approval** (usually 1-3 days)

## API Endpoints Used

The extension communicates with these backend endpoints:

**POST /api/mark-applied**
- Marks a job as applied
- Requires: X-Extension-Token header
- Body: { url, title, company, appliedAt }

**POST /api/save-job**
- Saves a job from extension
- Requires: X-Extension-Token header
- Body: { url, title, company, savedAt }

**GET /api/job-info**
- Gets job information by URL
- Requires: X-Extension-Token header
- Query: ?url=...

**GET /api/ping**
- Health check
- No authentication required

## Security Notes

- Extension token is sent in headers (not in URL)
- Only communicates with your JobWatch backend
- No data is sent to third parties
- All communication is over HTTPS (in production)

## Support

If you encounter issues:

1. Check browser console for errors (F12 → Console)
2. Check Flask app logs: `tail -f logs/scheduler.log`
3. Check database: `sqlite3 jobwatch.db "SELECT * FROM web_saves ORDER BY saved_at DESC LIMIT 5"`
4. Review this guide's troubleshooting section

---

**Happy automatic job tracking! 🚀**
