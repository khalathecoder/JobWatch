# JobWatch Scheduler Setup

The scheduler runs **independently** of the Flask web app.
It scans companies every 2 days and suggests new ones on your configured interval —
whether or not you have the dashboard open.

---

## Windows Setup (One Time)

### Step 1 — Right-click `install_startup_windows.bat` → Run as Administrator

This registers the scheduler as a Windows Task that:
- Starts automatically when you log into Windows
- Runs silently in the background (no terminal window)
- Logs all activity to `scheduler.log`

### Step 2 — Done

The scheduler runs immediately when you log in, then every 2 days after.

---

## Starting Manually (without restarting)

Double-click `start_scheduler.bat`

Or from your activated venv:
```
pythonw scheduler.py
```
(`pythonw` runs without a terminal window)

---

## Checking if it's Running

Open Task Manager → Details tab → look for `pythonw.exe`

Or check the log:
```
type scheduler.log
```

---

## Viewing the Log

The scheduler writes to `scheduler.log` in the jobwatch folder:
```
2026-05-23 08:00:01  INFO  ── Scheduled scan starting ──
2026-05-23 08:00:04  INFO  [WORKDAY] Cleveland Clinic
2026-05-23 08:00:07  INFO  [WORKDAY] Progressive Insurance
2026-05-23 08:00:21  INFO  Scan complete — 11 companies, 4 new jobs queued
2026-05-23 08:00:23  INFO  Scoring complete
```

---

## Removing from Startup

Double-click `uninstall_startup_windows.bat`

---

## Changing Scan Frequency

Edit `scheduler.py`, find this line:
```python
scan_interval_days = 2
```
Change to whatever you want. Restart the scheduler.

Or change `suggestion_interval` in the dashboard Settings page —
the scheduler reads it from your settings on next startup.

---

## The Two Processes

| Process | What it does | How to start |
|---|---|---|
| `app.py` | Flask dashboard at localhost:5050 | `python app.py` |
| `scheduler.py` | Background scanner + suggester | Auto on login, or `start_scheduler.bat` |

They share the same `jobwatch.db` database. You can run both at the same time.
