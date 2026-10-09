@echo off
setlocal
cd /d "%~dp0"

set "GODOT_EXE=C:\Users\ASM\Desktop\Godot_v4.6.3-stable_win64.exe"

if not exist "%GODOT_EXE%" (
    echo Godot not found.
    pause
    exit /b 1
)

start "ASM67 Godot" "%GODOT_EXE%" --path "%CD%" --fullscreen
timeout /t 5 /nobreak >nul

echo Starting MPF...
where mpf
call mpf -tv

pause