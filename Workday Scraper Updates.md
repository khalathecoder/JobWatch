# Workday Scraper Updates

I have expanded the Workday scraper to include more companies and industries, and implemented a dynamic discovery mechanism to find new companies automatically.

## 1. Expanded Company List
The `scraper.py` file has been updated with several new healthcare and tech companies that use Workday.

| Company | Tenant | Career Site | Industry |
|---|---|---|---|
| **Phreesia** | phreesia | Phreesia | Healthcare Tech |
| **Owens & Minor** | owensminor | OMCareers | Healthcare Logistics |
| **CVS Health** | cvshealth | CVS_Health_External_Career_Site | Healthcare/Retail |
| **McKesson** | mckesson | McKesson_External_Career_Site | Healthcare/Pharma |
| **Johnson & Johnson** | jnj | JNJ_External_Career_Site | Healthcare/Pharma |
| **Medtronic** | medtronic | Medtronic_External_Career_Site | Healthcare Tech |
| **iScribeHealth** | (HTML) | https://www.iscribehealth.com/careers | Healthcare AI |

## 2. Dynamic Company Discovery
I added a new function `discover_new_companies()` to `scraper.py` that uses Claude with web search to find new companies across various industries (healthcare, finance, tech) that use Workday.

- **How it works**: It searches for large companies in the target sectors, identifies their Workday career site URLs, and adds them to the `company_suggestions` table for your review.
- **Integration**: This discovery logic is now integrated into the scheduled scan in `scheduler.py`, meaning the app will automatically look for new targets every time it runs.

## 3. Improved Discovery Logic
The `run_scrape()` function in `scraper.py` now accepts a `discover` parameter. When set to `True`, it triggers the new discovery process before scanning the existing companies.

## 4. Discovered Companies Reference
I created a reference file `/home/ubuntu/JobWatch/discovered_companies.md` containing a list of potential new targets and their configurations for future expansion.

## Next Steps
- **Review Suggestions**: Check the "Companies" tab in your dashboard to approve or reject the newly discovered companies.
- **Verify iScribeHealth**: Since iScribeHealth uses a custom careers page (not Workday), I've added it as an HTML target. You may want to monitor its performance and consider a more specific scraper if needed.
- **Industry Expansion**: The discovery logic is currently set to find 5 companies per run. You can adjust this number or the target sectors in `scraper.py` to broaden the search further.
