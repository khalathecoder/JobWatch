# JobWatch — Project Context for Claude Code

## Who I Am
- **Name:** Khala Wright
- **Location:** Cleveland Heights, OH
- **Background:** Production Support Engineer at Solventum (formerly 3M Health IT)
  - Daily tools: SailPoint, CyberArk, Azure, KQL, SQL Server, PowerShell, C#/.NET
  - Run daily scrum + biweekly sprint reviews
- **Goal:** Pivot into cybersecurity (SOC Analyst II, Detection Engineer, SIEM Engineer, Vulnerability Management)
- **Education:** M.S. Cybersecurity & Information Assurance — WGU, May 2026
- **Certs:** CompTIA CySA+, CompTIA PenTest+ (PT0-003)
- **GitHub:** github.com/khalathecoder

---

## What JobWatch Is
A **private, password-protected Flask dashboard** that:
1. Scrapes healthcare and financial company career pages for cybersecurity job listings
2. Filters by security keywords (SIEM, SOC, IAM, vulnerability, etc.)
3. Shows matched jobs in a dashboard with status tracking (new → saved → applied → rejected)
4. Has an **Autofill Sidebar** that slides in when clicking "Apply / Autofill" on a job card
5. The sidebar has Resume A (Security) and Resume B (Support/Dev) toggle with all fields copyable

---

## Project Structure
```
jobwatch/
├── app.py              ← Flask app, all routes, auth
├── database.py         ← SQLite — jobs, scan logs, stats
├── profile_db.py       ← SQLite — profile info, experience, education, skills
├── profile_data.py     ← Seed data pre-loaded from Khala's resume
├── scraper.py          ← Workday JSON API scraper + HTML fallback
├── requirements.txt
├── .env                ← SECRET_KEY, DASHBOARD_PASSWORD, DASHBOARD_USERNAME
├── resumes/            ← Drop .docx/.pdf files here, served via /resumes/<filename>
└── templates/
    ├── base.html       ← Design system, CSS variables, shared styles
    ├── login.html      ← Login page
    ├── dashboard.html  ← Main job listing dashboard
    ├── sidebar.html    ← Autofill sidebar component (included in dashboard)
    └── profile.html    ← Profile editing page at /profile
```

---

## Tech Stack
- **Backend:** Python 3, Flask, Flask-Login, Werkzeug (bcrypt)
- **Database:** SQLite (jobwatch.db — auto-created on first run)
- **Scraping:** requests + BeautifulSoup4, Workday JSON API
- **Scheduling:** APScheduler (available, not yet wired for auto-scan)
- **Frontend:** Vanilla HTML/CSS/JS, Google Fonts (DM Mono + Sora)
- **Auth:** Single-user, bcrypt password hash, Flask-Login sessions

---

## Design System (base.html CSS variables)
```css
--bg:       #0B0F14   /* page background */
--surface:  #131920   /* topbar, cards */
--card:     #1A2230   /* inner cards, fields */
--border:   #243040
--accent:   #2E72C2   /* steel blue */
--accent2:  #1B4F8A
--text:     #DDE6F0
--muted:    #6B7F96
--new:      #3FB950   /* green */
--saved:    #E3B341   /* yellow */
--applied:  #58A6FF   /* blue */
--rejected: #F85149   /* red */
--mono:     'DM Mono', monospace
--sans:     'Sora', sans-serif
```

---

## Scraping Architecture

### Workday companies (reliable JSON API)
POST to `https://{tenant}.wd5.myworkdayjobs.com/wday/cxs/{tenant}/{career_site}/jobs`
Returns `jobPostings[]` with title, externalPath, locationsText, postedOn.

**Current Workday targets:**
| Company | Tenant | Career Site |
|---|---|---|
| Cleveland Clinic | clevelandclinic | ClevelandClinic_External_Career_Site |
| Progressive Insurance | progressive | ExtProgressive |
| Elevance Health | elevancehealth | ANT |
| Humana | humana | Humana_External_Careers |
| UnitedHealth / Optum | uhg | Optum_Careers |
| FirstEnergy | firstenergycorp | FE_External |
| KeyBank | key | Key_External_Career_Site |

### HTML scrape companies (fragile — needs upgrading)
- University Hospitals → uses iCIMS (needs proper iCIMS API)
- MetroHealth → needs iCIMS or custom scraper
- Summa Health → needs custom scraper
- Oracle Health / Cerner → needs Taleo scraper

---

## Known Issues / Next Steps

### High Priority
- [ ] **iCIMS scraper** — University Hospitals and MetroHealth use iCIMS. Need proper API integration
- [ ] **Greenhouse scraper** — some smaller health tech companies use this
- [ ] **Taleo scraper** — Oracle Health / Cerner uses Taleo
- [ ] **Auto-scan scheduler** — APScheduler is installed, just needs wiring in app.py
- [ ] **Profile page** — email/phone fields are empty, need to be filled in manually at /profile

### Medium Priority
- [ ] **Match score** — compare job keywords against profile skills, show % fit on card
- [ ] **Resume auto-recommend** — A vs B suggestion based on job keyword analysis
- [ ] **Chrome extension v2** — float sidebar over any company career page without alt-tabbing

### Low Priority / Nice to Have
- [ ] **Email alerts** — notify when new jobs match keywords
- [ ] **Notes field** — add notes to a job card
- [ ] **Export** — export applied jobs to CSV

---

## Resume Versions
| File | Tag | Use For |
|---|---|---|
| `Khala_Wright_Resume_SecurityAnalyst.docx` | Security | SOC Analyst, Detection Engineer, SIEM, IAM, Vuln Management |
| `Khala_Wright_Resume_v2.docx` | Support / Dev | DevSecOps, Platform Engineer, Senior Support, .NET roles |

**Resume A title:** Security Operations Engineer  
**Resume B title:** Production Support Engineer

---

## Target Companies (by priority)
1. **University Hospitals** — Shaker Heights, OH (neighbor), actively building security team
2. **Progressive Insurance** — Mayfield Village, OH, pays tech salaries, remote friendly
3. **FirstEnergy** — Akron, OH, new CSO hired April 2026 = team building wave
4. **Cleveland Clinic** — prestige but lower pay, still worth applying
5. **Elevance Health / Anthem** — remote, massive security org
6. **Humana** — remote, strong security team
7. **UnitedHealth / Optum** — remote, always hiring security
8. **KeyBank** — Cleveland HQ, financial sector pay
9. **MetroHealth** — local, less competitive
10. **Oracle Health / Cerner** — Khala has direct EHR experience with their platform

---

## Coding Preferences
- Python: snake_case, clear variable names, inline comments on anything non-obvious
- SQL: lowercase keywords, declared variables at top, safety-first (no destructive ops without confirmation)
- HTML/CSS: CSS variables for all colors, no inline styles except spacing, semantic class names
- Keep functions small and single-purpose
- No over-engineering — practical > perfect

---

## How to Run
```bash
# Activate venv first
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# Run app
python app.py
# → http://localhost:5050
```

## How to Start a Claude Code Session
```bash
cd jobwatch
claude
```
Then say: **"Read CONTEXT.md and help me with [task]"**
