@echo off
setlocal enabledelayedexpansion
pushd "%~dp0"
title SL MTM Dashboard Launcher

echo ========================================================
echo   Dashboard Service Level MTM - Server Launcher
echo   PT Konimex ^& PT Menjangan Sakti
echo ========================================================
echo.

:: 1. Detect Python Executable
set "PY_CMD="
if exist "backend\venv\bin\python.exe" (
    set "PY_CMD=backend\venv\bin\python.exe"
) else if exist "backend\venv\Scripts\python.exe" (
    set "PY_CMD=backend\venv\Scripts\python.exe"
) else if exist "%~dp0backend\venv\bin\python.exe" (
    set "PY_CMD=%~dp0backend\venv\bin\python.exe"
) else if exist "%~dp0backend\venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0backend\venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo [1/3] Menggunakan Python: %PY_CMD%

:: 2. Free Port 5000 if occupied by zombie process
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    echo [2/3] Membersihkan proses lama pada port 5000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: 3. Start Standalone Server in a separate window
echo [3/3] Menjalankan Local Standalone Server (http://localhost:5000)...
start "SL MTM Dashboard Server" cmd /k call "%PY_CMD%" backend\app_standalone.py

echo Menunggu server siap...
timeout /t 3 /nobreak >nul

echo.
echo ========================================================
echo   Server Berjalan! Membuka Dashboard di Browser...
echo   URL: http://localhost:5000
echo ========================================================
echo.
start http://localhost:5000

echo Jendela ini dapat ditutup jika sudah selesai.
echo (Server akan tetap berjalan di jendela "SL MTM Dashboard Server").
pause >nul
popd
