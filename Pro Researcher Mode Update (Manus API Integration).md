# Pro Researcher Mode Update (Manus API Integration)

I have upgraded your JobWatch application with **"Pro Researcher" mode**. This mode moves beyond standard job boards like LinkedIn and Indeed by using the **Manus API** to perform deep, agentic research into high-quality enterprise companies.

## 1. How "Pro Researcher" Works
Instead of a simple keyword search, the system now triggers a full Manus agent to:
- **Discover Niche Opportunities**: Search for companies that hire for your specific toolset (SailPoint, CyberArk, Azure KQL).
- **Verify Career Portals**: The agent visits the actual career sites of companies to confirm they have active, remote roles.
- **Bypass Aggregators**: It focuses on direct employer sites (Workday, Greenhouse, Lever) rather than noisy job boards.
- **Tailored Justification**: For every company suggested, the agent provides a "Why Suggested" explanation based on your HIPAA-regulated Azure experience.

## 2. New Components
- **`manus_researcher.py`**: A new script that handles the connection to the Manus API, manages the research task, and processes the structured results.
- **`scraper.py` Upgrade**: The discovery logic now defaults to the Manus API if an API key is present, with a fallback to the basic LLM discovery.

## 3. How to Activate
To enable this high-quality discovery, you need to add your Manus API key to your `.env` file:
1.  Open your `.env` file in the `JobWatch` folder.
2.  Add this line:
    ```env
    MANUS_API_KEY=your_actual_api_key_here
    ```
3.  The next scheduled scan (every 2 days) will automatically use the "Pro Researcher" mode.

## 4. Outcomes
By moving beyond LinkedIn/Indeed, you can expect:
- **Higher Relevance**: Companies that actually use the tools you're expert in.
- **Less Competition**: Finding roles that aren't yet saturated on major job boards.
- **Enterprise Focus**: Targeting stable, large-scale employers in Healthcare, Finance, and Tech.

I've attached the updated code files. Simply replace your local versions with these to start using the new system.
