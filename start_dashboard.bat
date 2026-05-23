@echo off
SET SCRIPT_DIR=%~dp0
start "JobWatch Dashboard" "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%app.py"
timeout /t 2 >nul
start http://localhost:5050
