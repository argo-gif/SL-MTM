@echo off
echo ========================================================
echo   Dashboard Service Level MTM - Server Launcher
echo ========================================================
echo.
echo Starting Local Standalone Server (http://localhost:5000)...
echo.
start "SL MTM Dashboard Server" cmd /k "python backend/app_standalone.py"
echo Server launching in new window!
echo Access the Dashboard in your browser at: http://localhost:5000
echo.
pause
