@echo off
setlocal
cd /d "%~dp0"

set "GODOT_EXE=C:\Users\ASM\Desktop\Godot_v4.6-stable_win64.exe"

if not exist "%GODOT_EXE%" (
    echo Godot not found: %GODOT_EXE%
    pause
    exit /b 1
)

rem Start the Godot project.
start "ASM67 Godot" "%GODOT_EXE%" --path "%CD%" --fullscreen

rem Give Godot time to start its BCP server.
timeout /t 5 /nobreak >nul

rem Run MPF with your usual hardware command.  -t -vV for logs
mpf -t

rem To close both:
rem 1. **Godot:** press **Alt+F4** while its fullscreen window is active.
rem 2. **MPF:** select its console window and press **Ctrl+C** for a clean shutdown.
rem The batch file then pauses—press any key to close its window.

pause