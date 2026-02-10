@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Download static assets
echo Downloading Bootstrap Icons, Font Awesome, SortableJS to static...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\download_static_assets.ps1"
set EXIT_CODE=%errorlevel%
echo.
if %EXIT_CODE% neq 0 (
    echo Failed. Exit code: %EXIT_CODE%. Check network or path.
    echo If script execution is disabled, run in Admin PowerShell: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
) else (
    echo Done.
)
echo.
pause
