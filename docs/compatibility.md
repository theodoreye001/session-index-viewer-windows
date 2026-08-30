# Compatibility matrix

This document tracks the supported session sources and the platform-specific discovery rules used by Session Index Viewer v0.1.0.

| Source | Session storage | Windows path notes | Resume command |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/projects/*/*.jsonl` | `~` resolves to the current Windows user profile | `claude --resume <id>` |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` | Local visualization files under `~/.codex/visualizations` are proxied through localhost | `codex resume <id>` |
| Devin | platform-specific `devin/cli/sessions.db` | Windows default is `%APPDATA%\devin\cli\sessions.db`; `DEVIN_HOME` overrides discovery | `devin -r <id>` |
| Grok | `$GROK_HOME/sessions`, default `~/.grok/sessions` | Native Windows home paths are supported | `grok --resume <id>` |
| Pi | `~/.pi/agent/sessions/*/*.jsonl` | Native Windows home paths are supported | `pi --session <id>` |
| Copilot CLI | `~/.copilot/session-store.db` | Falls back to `~/.copilot/session-state/<id>/events.jsonl` | `copilot --resume <id>` |
| opencode | data directory `opencode/opencode.db` | Default Windows-compatible path is `~/.local/share/opencode/opencode.db`; supports `OPENCODE_DB` and `XDG_DATA_HOME` | `opencode --session <id>` |

## Working-directory normalization

The resume layer recognizes:

- native Windows paths such as `C:\Users\name\project`;
- forward-slash Windows paths such as `C:/Users/name/project`;
- WSL-mounted Windows homes such as `/mnt/c/Users/name/project`;
- macOS and Linux home paths;
- synchronized sessions whose recorded home-directory prefix belongs to another machine.

When a synchronized session refers to another user's home prefix, the relative suffix is mapped onto the current user's home when possible. Unmapped drive-root paths fall back conservatively to the current working directory rather than constructing an invalid path.

## Parser resilience

Session formats are owned by their respective CLI projects. The viewer uses conservative parsing and skips malformed or incomplete records where possible. Copilot event-log fallback specifically tolerates malformed physical JSONL lines so later valid messages remain discoverable.
