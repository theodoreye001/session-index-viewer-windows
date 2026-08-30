# Windows support

Windows is a first-class supported platform starting with v0.1.0 of this fork.

## Requirements

- Windows 11 or a comparable supported Windows environment.
- Python 3.11 or newer available through `py.exe` or `python.exe`.
- The AI CLI tools you want to browse and resume installed locally.
- Windows Terminal is recommended. The resume launcher falls back to `cmd.exe` when Windows Terminal is unavailable.

Node.js is optional for normal use. It is needed only when rebuilding the React frontend from source.

## Install

Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

The installer records the Python executable, optionally builds the React frontend, registers the viewer for the current user's logon, starts the server hidden, and verifies `http://127.0.0.1:7333/api/sessions`.

Task Scheduler is preferred. If current-user task registration is unavailable, installation falls back to a shortcut in the user's Startup folder.

Open the viewer at:

```text
http://127.0.0.1:7333
```

## Runtime files

Windows runtime state lives under:

```text
%LOCALAPPDATA%\session-index-viewer\
```

Typical files include:

```text
python.txt
install-mode.txt
server.pid
session-index-viewer.out.log
session-index-viewer.err.log
```

## Uninstall

From the repository root:

```powershell
.\uninstall.ps1
```

The uninstaller removes the autostart registration and stops the viewer process after verifying that the recorded PID belongs to this repository's `server.py`.

## Session data paths

| Source | Windows/default storage used by the viewer |
| --- | --- |
| Claude Code | `~/.claude/projects/*/*.jsonl` |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` |
| Devin | `%APPDATA%\devin\cli\sessions.db`, with `DEVIN_HOME` override |
| Grok | `%USERPROFILE%\.grok\sessions`, with `GROK_HOME` override |
| Pi | `%USERPROFILE%\.pi\agent\sessions\*\*.jsonl` |
| Copilot CLI | `~/.copilot/session-store.db`, with `session-state/*/events.jsonl` fallback |
| opencode | `%USERPROFILE%\.local\share\opencode\opencode.db`, with `OPENCODE_DB` and `XDG_DATA_HOME` overrides |

## Resume behavior

Resume commands are rebuilt server-side from validated source and session identifiers. Recorded working directories are normalized for native Windows paths, forward-slash Windows paths, WSL paths such as `/mnt/c/Users/...`, and sessions synchronized from another machine whose home-directory prefix differs.

When Windows Terminal is installed, the viewer opens a new terminal window for the selected session. Otherwise it starts `cmd.exe` with the validated resume command.

## Codex visualization images

Browser pages cannot load arbitrary `file:///` image references emitted in Codex replies. The backend rewrites Codex visualization references under `~/.codex/visualizations` to a localhost image endpoint.

The endpoint accepts only relative paths beneath that directory, restricts file types to common raster images, rejects traversal and absolute paths, and enforces a file-size limit.

## Verification

Run the full local test suite:

```powershell
py -m unittest discover -s tests -v
```

Check the service:

```powershell
Invoke-WebRequest http://127.0.0.1:7333/api/sessions?limit=1 -UseBasicParsing
```

Check the selected install mode:

```powershell
Get-Content "$env:LOCALAPPDATA\session-index-viewer\install-mode.txt"
```

If the value is `task`, inspect the scheduled task with:

```powershell
Get-ScheduledTask -TaskName "Session Index Viewer"
```

## Troubleshooting

If the viewer does not answer on port 7333, inspect:

```text
%LOCALAPPDATA%\session-index-viewer\session-index-viewer.err.log
```

If a session appears but Resume fails, verify that the corresponding CLI executable is available in `PATH` and that the resolved working directory exists on the current machine.
