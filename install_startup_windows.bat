@echo off
:: JobWatch Scheduler — Windows Task Scheduler installer
:: Right-click → Run as Administrator

SET SCRIPT_DIR=%~dp0
SET PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe
SET SCHEDULER=%SCRIPT_DIR%scheduler.py
SET TASK_NAME=JobWatchScheduler

IF NOT EXIST "%PYTHON%" (
    echo ERROR: venv not found at %PYTHON%
    echo Run: python -m venv venv  then  pip install -r requirements.txt
    pause
    exit /b 1
)

:: Remove existing task
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create task — runs every 2 days at 8am, repeats if missed
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON%\" \"%SCHEDULER%\"" ^
  /sc DAILY ^
  /mo 2 ^
  /st 08:00 ^
  /ru "%USERNAME%" ^
  /f

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo  JobWatch Scheduler registered in Task Scheduler.
    echo  Runs every 2 days at 8am automatically.
    echo  Log: %SCRIPT_DIR%scheduler.log
    echo.
    echo  To run it right now: start_scheduler.bat
    echo  To view in Task Scheduler: taskschd.msc
    echo  To remove: uninstall_startup_windows.bat
) ELSE (
    echo.
    echo  Failed. Try right-clicking and running as Administrator.
)
pause
