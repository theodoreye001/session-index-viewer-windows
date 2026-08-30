# session-index-viewer

**English** · [简体中文](README.zh-CN.md)

Current supported fork release: **v0.1.0**.

Local web viewer for AI coding CLI sessions on this machine. Browse sessions
from **Claude Code**, **Codex**, **Devin**, **Grok**, **Pi**, **Copilot CLI**,
and **opencode** in one place, search across tools, inspect token/tool usage
when metadata exists, and resume a session in a fresh terminal window.

<p align="center">
  <img src="docs/screenshot.jpg" alt="Session Index Viewer: browse and resume Claude Code / Codex / Devin / Grok / Pi / Copilot / opencode sessions" width="900" />
</p>

CLI resume pickers often show little more than a session ID and timestamp. This
viewer surfaces each session's opening prompt and latest reply so it is easier
to find the conversation you want to continue.

> **Windows and macOS supported.** Windows prefers Windows Terminal and falls
> back to a new CMD window when `wt.exe` is unavailable. macOS retains Ghostty,
> iTerm, and Terminal.app auto-detection. Linux backend compatibility is covered
> by CI, without a first-class installer or desktop terminal launcher guarantee.

Long-lived support docs: [Windows guide](docs/windows.md) ·
[Compatibility matrix](docs/compatibility.md) · [Support policy](SUPPORT.md) ·
[Release process](RELEASE.md).

## Run

### Windows

From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

The installer registers per-user login autostart and starts the viewer. It
prefers Task Scheduler and falls back to the current user's Startup folder.
Runtime state and logs live under:

```text
%LOCALAPPDATA%\session-index-viewer\
```

Open:

```text
http://127.0.0.1:7333
```

Uninstall:

```powershell
.\uninstall.ps1
```

Foreground-only use is also supported:

```powershell
py server.py
```

### macOS

```bash
./install.sh
open http://localhost:7333
```

Or run in the foreground with `python3 server.py`.

Frontend rebuild after UI changes is optional:

```bash
cd frontend && npm install && npm run build
```

`server.py` serves `frontend/dist/` when present and falls back to
`sessions-index.html` otherwise.

## Supported sources

| Source | Default path | Resume | Usage notes |
|--------|--------------|--------|-------------|
| Claude Code | `~/.claude/projects/*/*.jsonl` | `claude --resume <id>` | Lifetime sums from assistant `message.usage`; context ≈ peak input+cache |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` | `codex resume <id>` | Last cumulative `token_count`; context ≈ max per-turn total |
| Devin | Windows `%APPDATA%\devin\cli\sessions.db`; macOS `~/Library/Application Support/devin/cli/sessions.db`; Linux `~/.local/share/devin/cli/sessions.db` | `devin -r <id>` | Aggregated from `message_nodes`; `DEVIN_HOME` override supported |
| Grok | `$GROK_HOME/sessions` (default `~/.grok/sessions`) | `grok --resume <id>` | Mostly context-size data from disk; non-interactive one-shots are skipped |
| Pi | `~/.pi/agent/sessions/*/*.jsonl` | `pi --session <id>` | Sums each assistant turn's `message.usage`; context ≈ largest per-turn total |
| Copilot CLI | `~/.copilot/session-store.db`; fallback `~/.copilot/session-state/<id>/events.jsonl` | `copilot --resume <id>` | DB provides richer usage; event fallback keeps transcript/model/output/tool data available |
| opencode | `~/.local/share/opencode/opencode.db` | `opencode --session <id>` | Cumulative session token sums; `OPENCODE_DB` / `XDG_DATA_HOME` supported |

See [docs/compatibility.md](docs/compatibility.md) for platform-specific discovery
rules and working-directory normalization details.

Usage on each card is summarized as `ctx · out · tools · turns`. Click it, or
press **`u`** on the active card, for overview metrics, token mix, activity,
context pressure, and source-specific measurement notes.

**Context** means peak/window occupancy and should not be read as a full-session
billing total. Grok frequently exposes only a size signal.

## Codex local images

When a Codex reply contains a local visualization such as:

```text
file:///C:/Users/<user>/.codex/visualizations/...png
```

the viewer rewrites it to a restricted localhost media endpoint. That endpoint
only serves PNG, JPEG, WebP, GIF, and BMP files below the current user's
`~/.codex/visualizations` directory and rejects absolute paths, `..` traversal,
SVG, and oversized files.

## Keyboard

| Key | Action |
|-----|--------|
| `j` / `k` or arrows | Move active card |
| `Enter` | Resume in a terminal |
| `c` | Copy resume command |
| `p` | Pin / unpin |
| `u` | Open usage modal when usage exists |
| `⌘K` / `Ctrl+K` | Command palette |

## Pieces

- `server.py`: backend entry point bound to `127.0.0.1:7333`.
- `siv/`: stdlib-only backend.
  - `GET /` serves the viewer.
  - `GET /api/sessions?limit=1000` scans sessions with mtime/size caching.
  - `POST /api/resume` validates source/session/cwd and opens the platform terminal.
  - `GET /api/codex-visualization?path=...` safely proxies Codex local images.
  - Host/cwd mapping handles macOS, Linux, native Windows `C:\Users\...`, and WSL `/mnt/c/Users/...` paths.
  - Source adapters live under `siv/sources/`.
- `frontend/`: React card UI.
- `sessions-index.html`: single-file fallback when `frontend/dist` is absent.
- `install.ps1` / `run-windows.ps1` / `uninstall.ps1`: Windows install, autostart, runtime, and removal.
- `install.sh` / `uninstall.sh`: macOS launchd install and removal.
- `.github/workflows/tests.yml`: backend matrix, Windows install smoke test, and frontend build.

## Tests and release gate

Windows:

```powershell
py -m unittest discover -s tests -v
```

CI runs the backend suite on Windows, macOS, and Ubuntu. A separate Windows job
actually runs `install.ps1`, checks the HTTP endpoint and autostart registration,
and then runs `uninstall.ps1`. Releases also require a successful React
production build. See [SUPPORT.md](SUPPORT.md) and
[docs/release-checklist.md](docs/release-checklist.md) for the maintained gate.

## Multi-machine setup

If you sync session trees with Syncthing or a similar tool:

| Path | Sync-friendly? |
|------|----------------|
| `~/.claude/projects` | Yes, per-file JSONL |
| `~/.codex/sessions` | Yes, per-file JSONL |
| `~/.grok/sessions` | Yes when syncing session dirs while ignoring SQLite indexes and `*.lock` |
| `~/.pi/agent/sessions` | Yes, per-file JSONL |
| Devin `sessions.db` | **No**, a single SQLite DB cannot merge across machines |
| Copilot `session-store.db` | **No**, a single SQLite DB cannot merge across machines |
| opencode `opencode.db` | **No**, a single SQLite DB cannot merge across machines |

The viewer derives host labels from recorded working directories. Home-relative
paths from another machine can be remapped by suffix to the current user's home;
existing local drive-root paths such as `D:\...` are preserved verbatim.

Avoid writing the same session ID from two machines at the same time to prevent
conflict copies.

## Maintenance

The root `VERSION` file is the release version source for this fork. Release
notes for v0.1.0 live in [docs/release-v0.1.0.md](docs/release-v0.1.0.md), and
maintainer guidance lives in [docs/maintenance.md](docs/maintenance.md).
