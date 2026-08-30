# Support policy

Session Index Viewer supports local use on Windows and macOS.

## Supported platforms

| Platform | Support level | Installation | Resume behavior |
| --- | --- | --- | --- |
| Windows 11 / Windows Server 2025 class environments | Supported | `install.ps1` | Windows Terminal when available, `cmd.exe` fallback |
| macOS | Supported | `install.sh` | Ghostty, iTerm, or Terminal.app |
| Linux | Backend tested | Manual `python3 server.py` | No first-class desktop terminal launcher guarantee |

Python 3.11 or newer is the tested baseline. The backend uses only the Python standard library. The React frontend is optional at runtime because the server falls back to `sessions-index.html` when `frontend/dist/` is absent.

## Session sources

The viewer currently recognizes Claude Code, Codex, Devin, Grok, Pi, GitHub Copilot CLI, and opencode sessions. A source is shown only when its local session data exists.

Windows path compatibility is covered for native `C:\Users\...`, forward-slash Windows paths, WSL `/mnt/<drive>/Users/...` paths, and cross-machine home-directory remapping.

## Release gate

A release is considered supported when all of the following pass on the release commit:

1. Python unit tests on Windows, macOS, and Ubuntu.
2. PowerShell syntax validation for Windows installer scripts.
3. React frontend production build.
4. Windows install smoke test: install, HTTP health check, autostart registration, and uninstall.

## Known limitations

- Linux is exercised by CI for backend compatibility but does not yet have a dedicated installer or supported desktop terminal launcher.
- SQLite-backed sources such as Devin, Copilot, and opencode should not be merged across machines with file synchronization tools.
- Resume requires the corresponding CLI executable to be installed and available on `PATH`.
- Session formats belong to external CLI projects and may change. The viewer keeps defensive fallbacks where practical, including Copilot `session-state/*/events.jsonl` parsing.

## Reporting compatibility problems

When reporting a platform or parser problem, include the operating system, Python version, affected CLI and version, whether the session appears in `/api/sessions`, and the relevant error log. On Windows, logs live under `%LOCALAPPDATA%\session-index-viewer\`.
