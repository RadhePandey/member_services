@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found at "%CD%\venv"
    exit /b 2
)

if not exist "reports" mkdir "reports"
if not exist "screenshots" mkdir "screenshots"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "TIMESTAMP=%%I"
set "REPORT_PATH=reports\automation_report_%TIMESTAMP%.html"

echo Running the complete pytest suite...
"venv\Scripts\python.exe" -m pytest --html="%REPORT_PATH%" --self-contained-html %*
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
echo Consolidated HTML report: "%CD%\%REPORT_PATH%"
echo Failure screenshots: "%CD%\screenshots"
exit /b %TEST_EXIT_CODE%
