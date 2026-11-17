@echo off
cd /d "%~dp0"
title KKN - MODE SUBMIT
echo ============================================================
echo   MODE SUBMIT - FORM AKAN DISIMPAN KE WEBSITE
echo ============================================================
echo.
:konfirmasi
set "JAWABAN="
set /p "JAWABAN=data akan langsung tersubmit jika program ini dijalankan (Y/n) "
if not defined JAWABAN goto mulai
if /I "%JAWABAN%"=="Y" goto mulai
if /I "%JAWABAN%"=="N" exit /b 0
echo Masukkan Y untuk lanjut atau N untuk batal.
goto konfirmasi

:mulai
echo.
call "%~dp0_setup_dan_jalankan.bat"
if errorlevel 1 exit /b 1

echo.
echo [MULAI] Menjalankan program ...
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0kkn_log_harian_auto.py"
set "HASIL=%ERRORLEVEL%"

echo.
if not "%HASIL%"=="0" echo [ERROR] Program berhenti dengan kode %HASIL%.
echo Tekan tombol apa saja untuk menutup jendela ini.
pause >nul
exit /b %HASIL%
