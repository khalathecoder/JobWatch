# JobWatch Repository Analysis

This document provides an analysis of the `JobWatch` GitHub repository (`https://github.com/khalathecoder/JobWatch`) against the initial project breakdown provided by the user. The analysis aims to confirm the implementation of features, identify any discrepancies, and highlight areas for further development based on the repository's contents, primarily `CONTEXT.md` and `README.md`.

## 1. Core App

### User Breakdown:
> - Login-protected Flask dashboard at localhost:5050
> - Windows Task Scheduler setup — scheduler runs every 2 days, dashboard auto-starts on login
> - SQLite database — jobs, companies, queue, profile, preferences, web saves

### Repository Analysis:
The `README.md` confirms the **Flask dashboard** running at `http://localhost:5050` and its **password-protected** nature. The `app.py` file is identified as the main Flask application handling routes and authentication. The `database.py` and `profile_db.py` files indicate the use of **SQLite databases** for jobs, scan logs, stats, profile information, experience, education, and skills. The presence of `install_dashboard_startup.bat` and `install_startup_windows.bat` suggests the implementation of **Windows Task Scheduler setup** for auto-starting the dashboard and potentially scheduling tasks.

## 2. Scraping

### User Breakdown:
> - Workday JSON API (7 companies — CCF, Progressive, Elevance, Humana, Optum, FirstEnergy, KeyBank)
> - Greenhouse + Lever public APIs with description capture
> - HTML fallback for iCIMS and custom pages
> - ATS auto-detection from careers URL
> - Location filter — remote nationwide OR 50mi Cleveland radius
> - Title pre-filter — blocks non-SW disciplines and C-suite
> - Must-match and exclude keyword lists (configurable in Settings)

### Repository Analysis:
The `scraper.py` file is dedicated to scraping, and `CONTEXT.md` explicitly mentions **Workday JSON API** integration with a list of 7 target companies, matching the user's breakdown. It also notes **HTML fallback** for other companies, including iCIMS. The `location_filter.py` and `settings_db.py` (for configurable keyword lists) suggest the implementation of location and title filtering, as well as must-match and exclude keyword lists. The `CONTEXT.md` also lists known issues with iCIMS, Greenhouse, and Taleo scrapers, indicating these are areas for improvement.

## 3. Company Pipeline

### User Breakdown:
> - Claude suggests companies every 2 days across configurable sectors (web search enabled)
> - Approval queue — you approve/reject in dashboard
> - On approval → immediate scan fires in background
> - Watchlist with grace period — auto-rejects companies with no relevant listings after 14 days
> - Companies tab — Active / Watching / Auto-rejected views with grace period progress bar

### Repository Analysis:
The `company_pipeline.py` file is present, suggesting the implementation of a company pipeline. While `CONTEXT.md` doesn't explicitly detail the 
full functionality of Claude suggesting companies or the approval queue, the presence of this file indicates that this module is part of the project. The `README.md` mentions a "Scan" button to pull fresh job listings, which aligns with the idea of an immediate scan firing in the background.

## 4. Job Queue

### User Breakdown:
> - Jobs go through approval queue before hitting dashboard
> - Claude scores each job 1-10 using description + your profile + preference history
> - Configurable score threshold in Settings
> - Age badges — 🔥 48hrs / 🟢 7 days / 🟡 14 days / 🔴 30 days / 👻 archived
> - Auto-archive based on configurable threshold
> - Claude learns from every approve/reject decision

### Repository Analysis:
The `database.py` likely handles the storage of job data, including status and potentially scores. The `settings_db.py` would manage configurable thresholds for scores and archiving. While the explicit mention of "Claude" scoring and learning is not directly visible in the file structure, the `suggestions.py` file might be related to this functionality. The `dashboard.html` template would be responsible for displaying age badges and job statuses.

## 5. Autofill Sidebar (Flask version)

### User Breakdown:
> - Slides in from right on any job card
> - Resume A / B toggle
> - All profile fields one-click copyable — name, email, phone, location, LinkedIn, GitHub
> - Every job experience with dates, per-bullet copy (plain / bullet / HTML)
> - Cover letter generator — 2 paragraphs, pulls passion statement, tailored to job description

### Repository Analysis:
The `sidebar.html` template is explicitly mentioned in `CONTEXT.md` as the "Autofill sidebar component (included in dashboard)", confirming its existence. The `profile_db.py` and `profile_data.py` would provide the necessary profile information for autofill. The `README.md` mentions a "Get Resume" option, which aligns with the Resume A/B toggle. The cover letter generator functionality would likely be implemented within `app.py` or a related utility file.

## 6. Chrome Extension

### User Breakdown:
> - ⚡ floating button — opens autofill sidebar on any page
> - ＋ floating button — Save to JobWatch from any job page
> - Auto-reads job description from page DOM (15+ ATS selectors)
> - Resume A/B toggle
> - All autofill fields + cover letter generator
> - Badge count — red number shows pending saved jobs
> - Badge refreshes every 5 minutes via background alarm
> - Popup with connection status + dashboard/profile links

### Repository Analysis:
There are no explicit files related to a Chrome Extension in the provided repository structure. This suggests that the Chrome Extension is either a separate project not included in this repository or is still in the conceptual/planning phase. The initial breakdown lists it as a built and shipped component, which is a discrepancy.

## 7. Saved Jobs Page

### User Breakdown:
> - Jobs saved via extension land here
> - Staleness banner for 14+ day old jobs
> - Fresh / Stale / Applied / Archived filters
> - One-click mark applied or archive

### Repository Analysis:
The `saved_jobs.html` template confirms the existence of a dedicated page for saved jobs. The filtering and archiving functionalities would be handled by `app.py` interacting with `database.py`.

## 8. Profile

### User Breakdown:
> - Full profile editing at /profile
> - Personal info, summaries A/B, passion statement, all experience entries editable
> - Experience pre-seeded from resume

### Repository Analysis:
The `profile.html` template and `profile_db.py` confirm the presence of a profile editing page and the storage of profile information. `profile_data.py` is mentioned as containing seed data pre-loaded from the user's resume.

## 9. Settings

### User Breakdown:
> - Archive threshold, score threshold, suggestion interval, grace period
> - Sector toggles (chip UI)
> - Must-match and exclude keyword lists

### Repository Analysis:
The `settings.html` template and `settings_db.py` indicate the implementation of a settings page where these configurable options would be managed.

## 10. Known Gaps and Backlog

### User Breakdown:
> - **Known Gaps:** iCIMS scraper is weak, Greenhouse/Lever dynamic companies, Board token extraction from URL needs testing, `company_pipeline.py` orphaned file, Profile updates don't reflect in sidebar without restart, Profile cache in extension only refreshes on new page load, No email/phone in profile, Sensitive fields need to be filled manually, `CONTEXT.md` needs updating.
> - **Backlog:** Proper iCIMS API integration (High), Match score on job cards (Medium), Resume A/B auto-recommend per job (Medium), `CONTEXT.md` refresh (Low).

### Repository Analysis:
The `CONTEXT.md` file in the repository explicitly lists many of these known gaps and backlog items, confirming that the user is aware of these areas for improvement. The `company_pipeline.py` being an orphaned file is also noted in the `CONTEXT.md` within the repository. The `CONTEXT.md` itself states it needs updating, which is also in the backlog.

## Summary and Discrepancies

Overall, the GitHub repository largely aligns with the detailed breakdown provided by the user. The core application, scraping mechanisms (especially Workday), company pipeline (though details on Claude's role are less explicit in the code structure), job queue, autofill sidebar, saved jobs page, profile, and settings are all represented in the file structure and `CONTEXT.md`.

The most significant discrepancy is the **Chrome Extension**. While the user's initial breakdown lists it as "Built & Shipped," there are no corresponding files or directories in the GitHub repository to support its existence within this project. It is possible the Chrome Extension is a separate repository or was not pushed to this one.

Another point to note is the explicit mention of "Claude" for company suggestions, job scoring, and learning from decisions. While `suggestions.py` exists, the direct integration with an LLM like Claude is not immediately apparent from the file names alone and would require deeper code inspection.

**Next Steps:**

1.  **Clarify Chrome Extension**: Confirm if the Chrome Extension is in a separate repository or if its files need to be added to this one.
2.  **Deep Dive into Claude Integration**: If the user wishes, a deeper analysis of `suggestions.py` and related files can be performed to understand the current implementation of Claude-like functionalities.
3.  **Address Known Gaps**: Prioritize and begin addressing the high-priority known gaps, such as the iCIMS scraper integration.

This analysis provides a solid foundation for understanding the JobWatch project and moving forward with development and improvements.
