@echo off
setlocal
cd /d "%~dp0"
title ASM67 Test Issue Tracker
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tracker_server.ps1"
echo.
echo Tracker stopped.
pause
