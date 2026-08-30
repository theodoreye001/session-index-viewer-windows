# Changelog

## v0.1.0 - 2026-08-30

### Windows support
- **Native session discovery and resume.** Added Windows Terminal launch with a
  CMD fallback while preserving the existing macOS Ghostty/iTerm/Terminal.app
  behavior. Claude Code and Codex discovery plus Codex resume were verified on
  a real Windows machine.
- **Cross-platform cwd handling.** Host labels and resume cwd mapping now accept
  native Windows paths, forward-slash Windows paths, macOS/Linux homes, and WSL
  `/mnt/<drive>/Users/...` paths.
- **Windows install/autostart.** Added `install.ps1`, `run-windows.ps1`, and
  `uninstall.ps1`. The installer prefers a per-user Scheduled Task, falls back
  to the Startup folder, keeps runtime state/logs in LocalAppData, and verifies
  the localhost service after start.

### Local media
- **Codex visualization proxy.** Local `file:///.../.codex/visualizations/...`
  image references are rewritten to a restricted localhost endpoint. The
  endpoint allows common raster image formats below the visualization root and
  rejects traversal, absolute paths, SVG, missing files, and oversized files.

### Sources
- **Windows-aware Devin path.** Devin for Terminal now resolves to
  `%APPDATA%\devin\cli` on Windows, Application Support on macOS, and the XDG
  data path on Linux. `DEVIN_HOME` is supported as an override.
- **Copilot durable-event fallback.** `session-store.db` remains the preferred
  fast path, with `~/.copilot/session-state/<id>/events.jsonl` used when the DB
  is missing, empty, or incompatible.
- **OpenCode overrides.** The viewer now honors `OPENCODE_DB` and
  `XDG_DATA_HOME` while retaining the default `~/.local/share/opencode` store.

### Validation
- **Cross-platform CI.** Added backend tests on Windows, macOS, and Ubuntu,
  frontend build verification, PowerShell parser checks, and a Windows smoke
  job that performs an actual install, HTTP health check, autostart validation,
  and uninstall.
- **Formal support policy.** Added versioning, release notes, a permanent
  Windows guide, a compatibility matrix, a support policy, and a repeatable
  release checklist for the maintained fork.

## 2026-08-17

### Sources
- **Three new session sources.** Added adapters for **Pi**
  (`~/.pi/agent/sessions/*/*.jsonl`, per-file JSONL like Codex),
  **Copilot CLI** (`~/.copilot/session-store.db`, SQLite `turns` +
  `assistant_usage_events`), and **opencode**
  (`~/.local/share/opencode/opencode.db`, SQLite `message`/`part`).
  Each is searchable, resumable (`pi --session`, `copilot --resume`,
  `opencode --session`), and reports token/tool usage. Source filter,
  accent colours, and context-window limits updated accordingly.

### Performance
- **Skeleton loading state.** The board now renders shimmer placeholder
  cards while `/api/sessions` is in flight instead of a blank
  "Loading…" line, so the first paint no longer looks frozen (respects
  `prefers-reduced-motion`).
- **Faster Devin refetch.** The Devin adapter only re-aggregates
  `message_nodes` usage for sessions whose `last_activity_at` changed.
  A warm `/api/sessions` (e.g. on tab refocus) dropped from ~0.65s to
  ~0.09s with no change to reported usage.

## 2026-08-11

### Performance
- **Virtual list.** The session board now uses
  [`@tanstack/react-virtual`](https://tanstack.com/virtual) window
  virtualization — only visible cards are mounted in the DOM, and
  variable card heights are measured per-item via `measureElement`.
  `SessionCard` is wrapped in `React.memo` with stable `useCallback`
  props so unchanged cards skip re-render. This keeps the UI smooth
  with the new 1000-session limit.
- **Window-scrolled layout.** Switched from a container-scrolled
  virtualizer to `useWindowVirtualizer` so the hero section scrolls
  away naturally with the page instead of being frozen at the top.
  A back-to-top button (↑) appears in the bottom-right after
  scrolling past the hero.

### Usage modal
- **Context pressure bar.** The usage modal now shows a colour-coded
  progress bar comparing peak context tokens against the model's
  context window limit. Green (< 60 %), yellow (60–85 %), red
  (≥ 85 %). Model → limit mapping is prefix-based and covers Claude,
  GPT/Codex, GLM, Gemini, Grok, DeepSeek, Kimi, and SWE variants,
  including 1 M-context variants.
- **Global single-instance modal.** `UsageModal` state was lifted
  from per-card to the App level so multiple modals can no longer
  stack on top of each other.

### Session limit
- **100 → 1000 sessions.** The default and maximum scan limits were
  raised from 100 / 500 to 1000 / 1000 across the backend
  (`siv/config.py`), frontend API client, and legacy shell indexer.
  This makes older sessions searchable without sacrificing
  responsiveness (virtual list + mtime/size cache).

### Terminal launch
- **Clean Ghostty windows.** Ghostty is now launched with
  `--window-save-state=never` so new terminal instances don't
  inherit the layout of previously closed windows.
