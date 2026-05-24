# Scheduling Configuration for Dynamic Company Discovery

The JobWatch application is now configured to perform dynamic company discovery every **2 days**, aligning with your request.

## Implementation Details

1.  **`scheduler.py`**: This file manages the scheduled tasks for JobWatch. It uses `apscheduler` to run functions at specified intervals.
2.  **`scan_interval_days`**: In `scheduler.py`, the `scan_interval_days` variable is set to `2`.
    ```python
    scan_interval_days = 2
    ```
3.  **`run_scan()` Function**: The `run_scan()` function, which now includes the call to `run_scrape(discover=True)`, is scheduled to execute based on the `scan_interval_days`.
    ```python
    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(days=scan_interval_days),
        id=\'company_scan\',
        name=\'Scan all watchlist companies\',
        replace_existing=True
    )
    ```

This setup ensures that every two days, your JobWatch application will:

*   Execute the `run_scan()` function.
*   Within `run_scan()`, it will call `run_scrape(discover=True)`.
*   The `discover=True` parameter will trigger the `discover_new_companies()` function, which uses Claude with web search to find new companies relevant to your updated resume profile.
*   These newly discovered companies will be added to your `company_suggestions` table for review in your dashboard.

## Next Steps

No further code changes are required for the scheduling. The system is now set up to automatically discover new companies every two days. You can monitor the `scheduler.log` file for execution details and check your JobWatch dashboard for new company suggestions.
