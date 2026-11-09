@echo off
chcp 65001 >nul 2>nul
set PYTHONUTF8=1
title Pipeline Command Center
cd /d "%~dp0"

echo ============================================
echo   Pipeline Command Center - One Click Start
echo   Docs: README.md  (Chinese)
echo ============================================

where py >nul 2>nul
if %errorlevel%==0 (
    echo [i] starting with py -3 ...
    py -3 server.py
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    echo [i] starting with python ...
    python server.py
    goto :end
)
where python3 >nul 2>nul
if %errorlevel%==0 (
    echo [i] starting with python3 ...
    python3 server.py
    goto :end
)

echo [ERROR] Python not found!
echo.
echo Install Python 3.9+: https://www.python.org/downloads/
echo IMPORTANT: check "Add python.exe to PATH" during install.
echo.
pause
exit /b 1

:end
echo.
echo Server stopped. Press any key to close this window...
pause >nul
