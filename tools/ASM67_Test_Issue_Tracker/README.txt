ASM67 TEST ISSUE TRACKER — WINDOWS + PHONE EDITION
===================================================

What this version changes
-------------------------
This build does NOT require Python.
It runs a small local web server using Windows PowerShell / .NET, which is
already included with normal Windows 10/11 installations.

The tracker runs on one Windows computer. Your iPhone or other phone connects
to that same tracker through Safari/Chrome over your local Wi-Fi. Both devices
see and edit the same issue list.

START
-----
1. Extract the ZIP somewhere writable, for example:
       C:\ASM67_Test_Issue_Tracker

2. Double-click:
       START_TRACKER.bat

3. A Command Prompt / PowerShell window remains open while the tracker runs.
   Your desktop browser opens automatically.

4. The window and the tracker page show the phone address, for example:
       http://192.168.1.50:8767/

5. Put the phone on the same Wi-Fi and either:
   - scan the QR code shown on the tracker page, or
   - type the displayed address into Safari/Chrome.

6. On iPhone, Safari -> Share -> Add to Home Screen if you want an app-like icon.

If the phone cannot connect
---------------------------
Windows Firewall may block incoming connections the first time.

Right-click:
       OPEN_FIREWALL.bat
and choose:
       Run as administrator

It adds a Private-network firewall rule for TCP port 8767.
Then restart START_TRACKER.bat and try the phone again.

The server uses a raw .NET TCP listener, so there is no HttpListener URL ACL
setup and no Python/Node dependency.

STOP
----
Press Ctrl+C in the tracker server window, or close that window.

DATA
----
Issues are stored in:
       data\issues.json

Back up that file to preserve your tracker database.
The file is plain JSON and can be inspected or recovered without special tools.

IMPORTANT: keep the tracker folder somewhere the Windows user can write to.
Do not run it directly from inside the ZIP.

WORKFLOW
--------
1. Choose Mode, Type, Area and Priority.
2. Enter a short title and optional notes/reproduction steps.
3. Add Issue.
4. Move issues through:
       New -> Confirmed -> In Progress -> Fixed -> Retest -> Complete
5. "Fixed" means code changed.
6. "Complete" should mean verified on the physical machine.

PHONE UI
--------
The layout changes to stacked issue cards on small screens.
The quick-add form and status controls remain available on the phone.

COPY FOR CHATGPT
----------------
Copies the currently filtered issue list into a compact format for pasting into
ChatGPT. A fallback copy method is included for iOS/local HTTP environments.

EXPORTS
-------
Export Markdown -> ASM67_CURRENT_TODO.md
Export CSV      -> ASM67_test_issues.csv

Exports honor the currently selected filters.

CONFIGURATION
-------------
config.json contains:
- server port (default 8767)
- mode dropdown entries
- issue types
- areas
- priorities
- statuses

You can edit those lists with Notepad while the tracker is stopped.

FILES
-----
START_TRACKER.bat      normal launcher; no Python required
OPEN_FIREWALL.bat      optional one-time Windows firewall setup
tracker_server.ps1     PowerShell/.NET local web server + JSON API
config.json            dropdown lists and port
static\index.html      web UI
static\style.css       desktop + phone styling
static\app.js          tracker UI behavior
static\qrcode.bundle.js local QR generator (no internet needed)
data\issues.json       created automatically on first run
QR_CODE_LICENSE.txt    MIT license for embedded QR generator source
