# Windows Step 5: source compatibility

This step audits the non-Claude/Codex adapters against their current session
storage layouts and adds Windows-specific path handling where needed.

## Compatibility matrix

| Source | Windows storage used by viewer | Resume command | Status |
| --- | --- | --- | --- |
| Claude Code | `%USERPROFILE%\.claude\projects\*\*.jsonl` | `claude --resume <id>` | Windows machine verified |
| Codex | `%USERPROFILE%\.codex\sessions\...\rollout-*.jsonl` | `codex resume <id>` | Windows machine verified |
| Pi | `%USERPROFILE%\.pi\agent\sessions\*\*.jsonl` | `pi --session <id>` | path/command compatible |
| Grok | `%USERPROFILE%\.grok\sessions\...` or `GROK_HOME` | `grok --resume <id>` | path/command compatible |
| Copilot CLI | `%USERPROFILE%\.copilot\session-store.db`, fallback `%USERPROFILE%\.copilot\session-state\<id>\events.jsonl` | `copilot --resume <id>` | DB plus durable-event fallback |
| OpenCode | `%USERPROFILE%\.local\share\opencode\opencode.db` | `opencode --session <id>` | Windows path compatible |
| Devin for Terminal | `%APPDATA%\devin\cli\sessions.db` | `devin -r <id>` | Windows path fixed in Step 5 |

## Devin platform paths

The viewer now resolves Devin for Terminal data per platform:

```text
Windows: %APPDATA%\devin\cli
macOS:   ~/Library/Application Support/devin/cli
Linux:   ~/.local/share/devin/cli
```

`DEVIN_HOME` overrides auto-detection when set.

## OpenCode overrides

OpenCode keeps its XDG-style data directory on Windows as well. The viewer now
honors:

```text
OPENCODE_DB
XDG_DATA_HOME
```

The default remains:

```text
~/.local/share/opencode/opencode.db
```

## Copilot CLI fallback

Current Copilot CLI documentation identifies:

```text
~/.copilot/session-state/<session-id>/events.jsonl
```

as the durable session history used for resume. `session-store.db` remains the
preferred viewer source because it provides denormalized turns and richer usage
metrics. If that DB is missing, empty, or incompatible, the viewer now scans the
event logs.

The fallback extracts:

- session ID and cwd from `session.start`
- first/last `user.message`
- last textual `assistant.message`
- model and output tokens where present
- tool call count from `tool.execution_start`
- task summary from `session.task_complete`

Malformed JSONL physical lines are skipped so one interrupted write does not hide
the rest of a readable session.

Input/cache token totals are left as zero in event-only mode because those values
are not reliably persisted per assistant event. When `session-store.db` is
available, its richer usage data continues to win.

## Validation

Run:

```powershell
py -m unittest discover -s tests -v
```

Then restart the viewer and check only the sources installed on the machine.
Missing source directories are expected and are silently skipped.
