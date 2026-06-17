@echo off
echo =========================================
echo    Installing rbot AI Assistant
echo =========================================
echo.
set INSTALL_DIR=%USERPROFILE%\.local\bin
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying binary to permanent location: %INSTALL_DIR%...
copy rbot.exe "%INSTALL_DIR%\rbot.exe" /Y

echo Creating startup shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\rbot.lnk');$s.TargetPath='%INSTALL_DIR%\rbot.exe';$s.Arguments='run';$s.Save()"

echo.
echo =========================================
echo  rbot has been successfully installed!
echo  Location: %INSTALL_DIR%\rbot.exe
echo  It will start automatically when you log in.
echo =========================================
pause
