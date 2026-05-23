@echo off
schtasks /delete /tn "JobWatchScheduler" /f
echo JobWatch Scheduler removed from startup.
pause
