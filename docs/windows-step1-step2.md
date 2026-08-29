# Windows Step 1 + Step 2 validation

This branch adds the first Windows-native path for Session Index Viewer.

## Step 1: verify read-only session discovery

Requirements:

- Python 3.10 or newer
- At least one supported CLI with local sessions, preferably Codex or Claude Code

From PowerShell in the repository root:

```powershell
py server.py
```

If `py` is unavailable:

```powershell
python server.py
```

Open:

```text
http://127.0.0.1:7333
```

Verify that existing Codex and Claude Code sessions appear and that title/text/usage fields load correctly.

The current scanner uses `os.path.expanduser("~")`, so the existing globs resolve under the Windows user profile, including:

```text
%USERPROFILE%\.codex\sessions\...\rollout-*.jsonl
%USERPROFILE%\.claude\projects\*\*.jsonl
```

## Step 2: verify Resume on Windows

The Windows launcher now:

1. resolves the recorded working directory;
2. builds the resume command as argv rather than a POSIX shell string;
3. prefers `wt.exe` when Windows Terminal is installed;
4. starts a new Windows Terminal window/tab in the session working directory;
5. falls back to a new `cmd.exe` console when Windows Terminal is unavailable.

Initial resume targets to verify:

```text
Codex:       codex resume <session-id>
Claude Code: claude --resume <session-id>
Pi:          pi --session <session-id>
```

In the viewer, select a session and press Enter or click Resume. A new terminal should open in the recorded project directory and resume that session.

You can also press `c` to copy the generated Windows command. It should look like:

```cmd
cd /d "D:\AI\Pyfluent" && codex resume <session-id>
```

## Known limitation for the next step

`host.py` still recognises Unix/macOS home prefixes for cross-machine host labels and cwd remapping. Native Windows drive-letter paths work when they exist locally, but Windows/WSL/cross-machine remapping will be addressed in Step 3.

## Automated tests

Run:

```powershell
py -m unittest discover -s tests -v
```

The current tests cover Codex/Claude/Pi argument construction, Windows copyable commands, Windows Terminal launch arguments, and the cmd.exe fallback.
