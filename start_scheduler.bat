@echo off
:: Run scheduler manually (no window — runs in background)
SET SCRIPT_DIR=%~dp0
START "" "%SCRIPT_DIR%venv\Scripts\pythonw.exe" "%SCRIPT_DIR%scheduler.py"
echo JobWatch Scheduler started in background.
echo Check scheduler.log for activity.
