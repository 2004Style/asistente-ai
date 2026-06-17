@echo off
echo =========================================
echo    Uninstalling rbot AI Assistant
echo =========================================
echo.
set INSTALL_DIR=%USERPROFILE%\.local\bin

echo Stopping rbot processes if running...
taskkill /F /IM rbot.exe >nul 2>&1

echo Removing files...
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\rbot.lnk" del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\rbot.lnk"
if exist "%INSTALL_DIR%\rbot.exe" del "%INSTALL_DIR%\rbot.exe"

echo.
echo =========================================
echo  rbot has been successfully uninstalled.
echo =========================================
pause
