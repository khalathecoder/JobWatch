# Resume and Role Expansion Updates

I have integrated your full resume profile into the JobWatch application and expanded the search and discovery logic to include **Product Support** and **Application Support** roles, matching your current experience at Solventum.

## 1. Full Resume Integration
The discovery and scoring prompts in `suggestions.py` and `scraper.py` now use the complete details from your **Security Analyst** resume:
- **Target Roles**: Security Analyst, Detection Engineer, SIEM & Compliance Specialist, Product Support Engineer.
- **Tools**: SailPoint IIQ, CyberArk PAM, Microsoft Sentinel, Azure KQL, Wazuh SIEM, Application Insights.
- **Experience**: 3+ years in HIPAA-regulated environments, investigating security events, and production support.
- **Education/Certs**: M.S. Cybersecurity (WGU 2026), CompTIA CySA+, PenTest+.

## 2. Expanded Search Keywords
I've updated `scraper.py` with new search terms and keywords to capture roles similar to your current production support position:
- **New Search Terms**: `product support engineer`, `application support engineer`, `platform support engineer`, `technical support engineer l3`, `site reliability engineer`.
- **New Keywords**: `production support`, `product support`, `application support`, `azure monitor`, `application insights`, `kql`, `troubleshooting`, `incident management`.

## 3. Enhanced Scoring Logic
The scoring algorithm in `suggestions.py` has been updated to:
- **Up-score** Production/Product Support Engineer roles that match your Azure/KQL background (+2 points).
- **Recognize** that you are highly qualified for senior support roles and score them normally without penalties.

## 4. Architectural Recommendation: Direct LLM
Based on your requirement to run discovery every 2 days, I recommend sticking with the **Direct LLM (Enhanced)** approach I've implemented.
- **Why**: It is significantly faster and more cost-effective than the Manus API for this specific frequency, while still being highly intelligent thanks to the detailed resume profile now embedded in the prompts.
- **Result**: Every 2 days, the scheduler will trigger a discovery run that uses Claude with web search to find 5 new companies tailored specifically to your background and preferences.

## Next Steps
- **Monitor the Dashboard**: You will now see a wider variety of relevant roles, including both security-focused and senior support positions.
- **Review New Suggestions**: The dynamic discovery will now prioritize companies that hire for both of your target areas.
