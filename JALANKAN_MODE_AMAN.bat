@echo off
cd /d "%~dp0"
title KKN - MODE AMAN (TANPA SUBMIT)
echo ============================================================
echo   MODE AMAN - FORM TIDAK AKAN DISIMPAN / DI-SUBMIT
echo ============================================================
echo.
call "%~dp0_setup_dan_jalankan.bat"
if errorlevel 1 exit /b 1

echo.
echo [MULAI] Menjalankan program ...
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0kkn_log_harian_auto.py" --dry-run
set "HASIL=%ERRORLEVEL%"

echo.
if not "%HASIL%"=="0" echo [ERROR] Program berhenti dengan kode %HASIL%.
echo Tekan tombol apa saja untuk menutup jendela ini.
pause >nul
exit /b %HASIL%
