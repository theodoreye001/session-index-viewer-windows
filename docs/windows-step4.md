# Windows Step 4: install and autostart

Step 4 adds a user-level Windows installation flow. The repository stays in its
current location; the installer registers that checkout to start the local viewer
when the current user signs in.

## Files

- `install.ps1`: resolves Python, optionally builds the React frontend, registers
  login autostart, starts the viewer, and reports health.
- `run-windows.ps1`: hidden runner used by Task Scheduler or the Startup-folder
  fallback. It writes the server PID and redirects logs under LocalAppData.
- `uninstall.ps1`: stops only a verified `server.py` process from this checkout,
  removes autostart registration, and cleans installation state/logs.

## Install

From PowerShell in the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

If Node/bun is unavailable, installation continues and `server.py` falls back to
`sessions-index.html`. To skip frontend build intentionally:

```powershell
.\install.ps1 -SkipFrontendBuild
```

The preferred autostart mechanism is a current-user Scheduled Task named:

```text
Session Index Viewer
```

The task uses `MultipleInstances=IgnoreNew`, starts at user logon, is allowed on
battery, has no execution time limit, and may restart after failure. If task
registration is unavailable or denied, the installer creates a user Startup
folder shortcut instead.

## Runtime files

Installation state and logs are stored in:

```text
%LOCALAPPDATA%\session-index-viewer\
```

Important files:

```text
python.txt
server.pid
session-index-viewer.out.log
session-index-viewer.err.log
install-mode.txt
```

The viewer remains bound to:

```text
http://127.0.0.1:7333
```

## Validation

After installation:

```powershell
Invoke-WebRequest http://127.0.0.1:7333/api/sessions?limit=1 -UseBasicParsing
```

Expected status is `200`.

Check the autostart mode:

```powershell
Get-Content "$env:LOCALAPPDATA\session-index-viewer\install-mode.txt"
```

For Task Scheduler mode:

```powershell
Get-ScheduledTask -TaskName "Session Index Viewer"
```

The task should exist and normally show `Running` while the viewer is active.

Also verify:

1. `http://127.0.0.1:7333` loads after closing the original manual `py server.py`
   console and starting the registered task.
2. Codex and Claude sessions are still visible.
3. Codex Resume still opens Windows Terminal correctly.
4. Codex visualization images still render through `/api/codex-visualization`.

## Uninstall

```powershell
.\uninstall.ps1
```

To retain logs:

```powershell
.\uninstall.ps1 -KeepLogs
```

The uninstaller verifies the process command line contains this checkout's exact
`server.py` path before terminating it. It will not kill an unrelated process
merely because it uses port 7333.
