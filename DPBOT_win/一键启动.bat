@echo off
rem ===== DPbot ASCII Version Launcher =====
rem Set UTF-8 encoding
chcp 65001 >nul
color 0A

rem Request Admin Rights
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting admin privileges...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

echo.
echo DPbot Launcher - ASCII Version
echo ==============================
echo.

rem Check Python Installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not detected. Please install Python and add to PATH.
    echo Visit: https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

rem Check Required Files
if not exist "%~dp0Redis\redis-server.exe" (
    echo [ERROR] Redis server not found. Path: %~dp0Redis\redis-server.exe
    echo.
    pause
    exit /b
)

if not exist "%~dp0wxapi\wxapi.exe" (
    echo [ERROR] wxapi not found. Path: %~dp0wxapi\wxapi.exe
    echo.
    pause
    exit /b
)

if not exist "%~dp0app\main.py" (
    echo [ERROR] main.py not found. Path: %~dp0app\main.py
    echo.
    pause
    exit /b
)

echo [INFO] Starting services...
echo.

echo [STEP 1] Starting Redis server...
start "" "%~dp0Redis\redis-server.exe" "%~dp0Redis\redis.windows.conf"
echo [SUCCESS] Redis server started.
echo Waiting 3 seconds...
timeout /t 3 /nobreak > nul

echo.
echo [STEP 2] Starting wxapi service...
start "" "%~dp0wxapi\wxapi.exe"
echo [SUCCESS] wxapi service started.
echo Waiting 3 seconds...
timeout /t 3 /nobreak > nul

echo.
echo [STEP 3] Starting main.py...
cd "%~dp0app"

rem Check Python Dependencies
echo [INFO] Checking Python dependencies...
python -c "import requests, qrcode, json, urllib.parse" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Missing libraries. Trying to install...
    pip install requests qrcode Pillow urllib3 loguru cprint
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Auto-installation failed. Please run manually:
        echo pip install requests qrcode Pillow urllib3 loguru cprint
        echo.
        pause
        exit /b
    )
)

echo.
echo =====================================================
echo LOGIN INSTRUCTIONS:
echo [1] First-time users must login
echo [2] Type 'y' to scan QR code and login
echo [3] Type 'n' to skip login
echo =====================================================
echo.
echo Force login? (y/n): 
set /p force_login=
if /i "%force_login%"=="y" (
    echo [INFO] Starting with forced login...
    start "" cmd /k "chcp 65001 > nul && python main.py --force"
) else (
    echo [INFO] Starting in normal mode...
    start "" cmd /k "chcp 65001 > nul && python main.py"
)

echo.
echo [COMPLETED] All services started!
echo Please follow instructions in the new console window.
echo If you encounter issues, check documentation or contact the author.
echo.
pause 