import os
import time
import json
import requests
from database import get_conn, save_company_suggestion

MANUS_API_KEY = os.getenv('MANUS_API_KEY')
BASE_URL = "https://api.manus.ai/v2"

def run_manus_discovery():
    """
    Triggers a Manus API task to perform deep research for new companies.
    """
    if not MANUS_API_KEY:
        print("  [MANUS] Error: MANUS_API_KEY not found in environment.")
        return 0

    print("  [MANUS] Starting 'Pro Researcher' discovery task...")
    
    # Define the high-quality research prompt
    research_prompt = """
    Perform deep research to find 5-8 enterprise companies (500+ employees) that are currently hiring for:
    - Security Analysts / Detection Engineers
    - IAM Specialists (SailPoint, CyberArk)
    - Senior Product/Production Support Engineers (Azure, KQL, App Insights focus)
    
    CRITERIA:
    1. Focus on Healthcare, Finance, and Tech sectors.
    2. MUST have active REMOTE roles in the US.
    3. Identify their ATS (Workday, Greenhouse, Lever, etc.).
    4. Provide the direct link to their career portal.
    5. AVOID staffing agencies, MSSPs, or Indeed/LinkedIn aggregators.
    
    For each company, explain WHY it's a good match for someone with 3+ years in HIPAA-regulated Azure environments.
    """

    # Define the structured output schema
    schema = {
        "type": "object",
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" },
                        "sector": { "type": "string" },
                        "ats_type": { "type": "string", "enum": ["workday", "greenhouse", "lever", "icims", "other"] },
                        "career_url": { "type": "string" },
                        "ats_tenant": { "type": ["string", "null"] },
                        "ats_career_site": { "type": ["string", "null"] },
                        "why_suggested": { "type": "string" }
                    },
                    "required": ["name", "sector", "ats_type", "career_url", "ats_tenant", "ats_career_site", "why_suggested"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["companies"],
        "additionalProperties": False
    }

    # 1. Create the task
    try:
        resp = requests.post(
            f"{BASE_URL}/task.create",
            headers={"x-manus-api-key": MANUS_API_KEY, "Content-Type": "application/json"},
            json={
                "message": {"content": research_prompt},
                "structured_output_schema": schema
            }
        )
        resp_data = resp.json()
        if not resp_data.get('ok'):
            print(f"  [MANUS] Task creation failed: {resp_data.get('error')}")
            return 0
        
        task_id = resp_data['task_id']
        print(f"  [MANUS] Task created: {task_id}. Waiting for results...")

        # 2. Poll for completion (timeout after 10 mins)
        start_time = time.time()
        while time.time() - start_time < 600:
            time.sleep(30)
            msg_resp = requests.get(
                f"{BASE_URL}/task.listMessages",
                params={"task_id": task_id, "order": "desc"},
                headers={"x-manus-api-key": MANUS_API_KEY}
            )
            msg_data = msg_resp.json()
            if not msg_data.get('ok'):
                continue

            # Check for structured_output_result event
            for event in msg_data.get('events', []):
                if event['type'] == 'structured_output_result':
                    result = event['structured_output_result']
                    if result['success']:
                        return process_manus_results(result['value']['companies'])
                    else:
                        print(f"  [MANUS] Extraction failed: {result.get('error')}")
                        return 0
                
                # Also check status
                if event['type'] == 'status_update' and event['status'] == 'error':
                    print("  [MANUS] Task encountered an error.")
                    return 0

        print("  [MANUS] Task timed out.")
        return 0

    except Exception as e:
        print(f"  [MANUS] Integration error: {e}")
        return 0

def process_manus_results(companies):
    """
    Saves the high-quality Manus results to the database.
    """
    added = 0
    for co in companies:
        try:
            save_company_suggestion(
                name=co['name'],
                sector=co['sector'],
                ats_type=co['ats_type'],
                ats_tenant=co.get('ats_tenant'),
                ats_career_site=co.get('ats_career_site'),
                career_url=co['career_url'],
                hq='',
                why=co['why_suggested']
            )
            added += 1
            print(f"    [MANUS] Suggested: {co['name']} ({co['sector']})")
        except Exception as e:
            print(f"    [MANUS] Save error for {co['name']}: {e}")
    
    print(f"  [MANUS] Successfully added {added} high-quality suggestions.")
    return added

if __name__ == "__main__":
    # For testing: load .env and run
    from dotenv import load_dotenv
    load_dotenv()
    run_manus_discovery()
