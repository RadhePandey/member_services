@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found at "%CD%\venv"
    exit /b 2
)

if not exist "reports" mkdir "reports"
if not exist "screenshots" mkdir "screenshots"

set "PYTHON=venv\Scripts\python.exe"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "E2E_RUN_ID=%%i"
set "E2E_FINAL_STAGE="

echo.
echo ============================================================
echo CLAIM END-TO-END - STAGE 1
echo Afroj submission - Prabhat forwarding - RadhePandey forwarding
echo ============================================================
echo.

call "%PYTHON%" -m pytest tests\test_it_equipment_claim.py -k "test_user_can_submit_valid_it_equipment_claim" -q -s
if errorlevel 1 (
    echo.
    echo STAGE 1 FAILED. Approval stage was not started.
    exit /b 1
)

echo.
echo ============================================================
echo CLAIM END-TO-END - STAGE 2
echo RadhePandey approval and Sanchalan Setu e-sign completion
echo ============================================================
echo.

set "E2E_FINAL_STAGE=1"
call "%PYTHON%" -m pytest tests\test_it_equipment_claim.py -k "test_approver_starts_esign_approval" -q -s
if errorlevel 1 (
    echo.
    echo STAGE 2 FAILED.
    exit /b 1
)

echo.
echo ============================================================
echo CLAIM END-TO-END COMPLETED SUCCESSFULLY
echo ============================================================
exit /b 0
