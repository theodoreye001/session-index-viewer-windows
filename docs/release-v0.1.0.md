# v0.1.0 release notes

v0.1.0 is the first formally supported Windows release of this fork while retaining macOS behavior from the upstream project.

## Highlights

- Native Windows session path handling and cross-machine cwd remapping.
- Windows resume launcher with Windows Terminal support and `cmd.exe` fallback.
- `install.ps1`, hidden runtime launcher, current-user autostart registration, and `uninstall.ps1`.
- Safe localhost proxy for Codex visualization images referenced through local `file:///` paths.
- Windows-aware Devin data discovery with `DEVIN_HOME` override.
- Copilot CLI `session-state/*/events.jsonl` fallback when the SQLite session index is missing or incompatible.
- opencode path overrides through `OPENCODE_DB` and `XDG_DATA_HOME`.
- CI matrix covering Windows, macOS, and Ubuntu, plus frontend production build and a real Windows installation smoke test.

## Validation gate

The release candidate must pass on the final release commit:

- 42 Python unit tests on Windows, macOS, and Ubuntu.
- PowerShell parser validation for `install.ps1`, `run-windows.ps1`, and `uninstall.ps1`.
- React frontend production build.
- Windows install smoke test that installs the viewer, receives HTTP 200 from `/api/sessions`, verifies autostart registration, and uninstalls cleanly.

## Upgrade from the development branch

Users who tested the earlier `windows-step1-step2` branch can update to the release branch, stop any manually started `py server.py` process, and run `install.ps1` once to register the supported background installation.

Runtime state remains under `%LOCALAPPDATA%\session-index-viewer\`.

## Known limitations

- Linux remains backend-tested without a first-class installer or desktop terminal launcher.
- Resume still depends on each external CLI being installed and available on `PATH`.
- External CLI session schemas may change independently; parser compatibility is maintained on a best-effort basis with regression tests for known formats.
