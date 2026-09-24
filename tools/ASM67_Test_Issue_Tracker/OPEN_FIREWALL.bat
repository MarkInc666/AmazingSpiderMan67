@echo off
setlocal
set PORT=8767
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo This must be run as Administrator.
  echo Right-click OPEN_FIREWALL.bat and choose "Run as administrator".
  pause
  exit /b 1
)
netsh advfirewall firewall delete rule name="ASM67 Test Issue Tracker" >nul 2>&1
netsh advfirewall firewall add rule name="ASM67 Test Issue Tracker" dir=in action=allow protocol=TCP localport=%PORT% profile=private
if %errorlevel% equ 0 (
  echo.
  echo Firewall rule added for TCP port %PORT% on Private networks.
) else (
  echo.
  echo Could not add the firewall rule.
)
pause
