@echo off
setlocal
cd /d "%~dp0"
title Persiapan KKN Tematik Sampah Tuntas

set "PYTHON_EXE="

call :cari_python
if defined PYTHON_EXE goto python_siap

echo [PERSIAPAN] Python belum terpasang. Mengunduh Python 3.12 ...
where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Windows Package Manager tidak tersedia.
    echo         Pastikan Windows 10/11 sudah diperbarui, lalu coba lagi.
    goto gagal
)

winget install --exact --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto gagal

call :cari_python
if not defined PYTHON_EXE (
    echo [ERROR] Python sudah diinstal tetapi belum dapat ditemukan.
    echo         Tutup jendela ini, lalu klik launcher sekali lagi.
    goto gagal
)

:python_siap
echo [OK] Python ditemukan: %PYTHON_EXE%

if not exist "requirements.txt" (
    echo [ERROR] File requirements.txt tidak ditemukan di folder ini.
    goto gagal
)

if not exist ".venv\Scripts\python.exe" (
    echo [PERSIAPAN] Membuat virtual environment ...
    "%PYTHON_EXE%" -m venv ".venv"
    if errorlevel 1 goto gagal
)

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
echo [PERSIAPAN] Memasang dependencies ...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r "requirements.txt"
if errorlevel 1 goto gagal

echo [PERSIAPAN] Memastikan browser Chromium tersedia ...
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 goto gagal

echo.
echo [SELESAI] Persiapan berhasil.
exit /b 0

:cari_python
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE exit /b 0
for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if defined PYTHON_EXE exit /b 0
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
exit /b 0

:gagal
echo.
echo Persiapan gagal. Periksa koneksi internet, lalu coba lagi.
echo Tekan tombol apa saja untuk menutup jendela ini.
pause >nul
exit /b 1
