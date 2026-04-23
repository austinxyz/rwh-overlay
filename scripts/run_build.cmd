@echo off
REM Daily auto-build wrapper invoked by Windows Task Scheduler.
REM Logs to stock-kb-build.log in the overlay root (gitignored).
REM Exit code is propagated so Task Scheduler can surface failures.

set OVERLAY_DIR=%~dp0..
cd /d "%OVERLAY_DIR%"

set LOG=%OVERLAY_DIR%\build.log
echo [%date% %time%] Starting build > "%LOG%"
.venv\Scripts\python.exe scripts\build_stock_kb.py >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] Build finished with exit code %RC% >> "%LOG%"
exit /b %RC%
