@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found at "%CD%\venv"
    exit /b 2
)

if not exist "reports" mkdir "reports"
if not exist "screenshots" mkdir "screenshots"

rem Demo mode: visible browser and a pause before every action so each
rem step is easy to follow on screen. Override by setting these first,
rem e.g. "set BROWSER_SLOW_MO=0" for a fast run.
if not defined BROWSER_HEADLESS set "BROWSER_HEADLESS=false"
if not defined BROWSER_SLOW_MO set "BROWSER_SLOW_MO=800"

echo.
echo ============================================================
echo MEDICAL CLAIM - SUBMISSION, INITIATION AND APPROVAL
echo Prabhat submits a Medical claim for Radha Mohan Das Agrawal
echo and forwards it; kaushlendra ini approves with e-sign
echo ============================================================
echo.

call "venv\Scripts\python.exe" -m pytest tests\test_medical_claim.py -k "test_initiator_submits_and_forwards_medical_claim or test_approver_esign_approves_medical_claim" -q -s
if errorlevel 1 (
    echo.
    echo MEDICAL CLAIM FLOW FAILED.
    exit /b 1
)

echo.
echo ============================================================
echo MEDICAL CLAIM FLOW COMPLETED SUCCESSFULLY
echo ============================================================
exit /b 0
