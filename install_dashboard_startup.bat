@echo off
:: Registers the JobWatch dashboard to auto-start with Windows
:: Right-click → Run as Administrator

SET SCRIPT_DIR=%~dp0
SET PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe
SET APP=%SCRIPT_DIR%app.py
SET TASK_NAME=JobWatchDashboard

IF NOT EXIST "%PYTHON%" (
    echo ERROR: venv not found. Run setup first.
    pause
    exit /b 1
)

schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Runs at login, starts the Flask app in background
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON%\" \"%APP%\"" ^
  /sc ONLOGON ^
  /delay 0000:30 ^
  /ru "%USERNAME%" ^
  /f

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo  JobWatch Dashboard registered.
    echo  Opens automatically at login.
    echo  Visit http://localhost:5050 in your browser.
    echo.
    echo  To start it right now without restarting:
    echo  Double-click start_dashboard.bat
) ELSE (
    echo  Failed. Try running as Administrator.
)
pause
