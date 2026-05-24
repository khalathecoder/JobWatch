# JobWatch — Healthcare Security Job Tracker

Your private, password-protected dashboard for monitoring cybersecurity
job listings across healthcare and financial companies.

---

## Setup (5 minutes)

### 1. Install Python dependencies
```bash
cd jobwatch
pip install -r requirements.txt
```

### 2. Configure your credentials
```bash
cp .env.example .env
```
Open `.env` and set:
- `SECRET_KEY` — any long random string (e.g. mash your keyboard)
- `DASHBOARD_PASSWORD` — your login password
- `DASHBOARD_USERNAME` — your login username (default: khala)

### 3. Add your resumes
Drop your `.docx` or `.pdf` resume files into the `resumes/` folder.
Naming convention the app auto-detects:
- `Khala_Wright_Resume_SecurityAnalyst.docx` → tagged "Security"
- `Khala_Wright_Resume_v2.docx` → tagged "Support / Dev"

### 4. Run the app
```bash
python app.py
```
Open your browser to: **http://localhost:5050**

---

## Usage

1. **Login** with your username/password
2. **Scan** — click the ⟳ Scan button to pull fresh job listings
   - Scans Workday-based companies via their JSON API
   - Scans other companies via HTML parsing
   - Only saves jobs matching your security keywords
3. **Browse** — filter by status, company, or search by keyword
4. **Open Listing** — launches the original job posting in a new tab
5. **Get Resume** — opens the resume picker to download the right version
6. **Track** — set status to Saved → Applied → (Interview) → Offer/Rejected

---

## Companies Monitored

- University Hospitals (Cleveland)
- Cleveland Clinic
- Progressive Insurance
- Elevance Health (Anthem)
- Humana
- UnitedHealth / Optum
- MetroHealth
- Summa Health
- FirstEnergy
- KeyBank
- Oracle Health / Cerner

## Adding More Companies

Open `scraper.py` and add an entry to the `COMPANIES` list.
- For Workday companies: `type: 'workday'`, find the tenant name in their careers URL
- For other companies: `type: 'html'`, add the search URL

---

## Security Notes

- Only accessible on your local machine (bound to 127.0.0.1)
- Password is hashed with bcrypt — never stored in plaintext
- Session expires when browser closes (unless "remember me")
- To expose on your network, change `host='127.0.0.1'` to `host='0.0.0.0'`
  and add firewall rules accordingly
