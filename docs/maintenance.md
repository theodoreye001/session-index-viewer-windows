# Maintenance notes

## Branches

`master` is the supported release line. Feature and compatibility work should land through short-lived branches and pass the full CI gate before merge.

The historical `windows-step1-step2` branch was used to develop the initial Windows port. It should be treated as a migration branch after v0.1.0 is merged.

## Versioning

The fork uses semantic versioning through the root `VERSION` file. Windows support begins at `0.1.0`.

Patch releases are for compatibility fixes, parser repairs, installer corrections, and regressions that do not intentionally change the public behavior. Minor releases may add session sources, platform capabilities, or UI features.

## External CLI changes

Claude Code, Codex, Devin, Grok, Pi, GitHub Copilot CLI, and opencode own their session formats and resume interfaces. When one changes:

1. Reproduce against a minimal session fixture or sanitized local sample.
2. Add a regression test before modifying the parser.
3. Keep existing parser paths when practical so older sessions remain readable.
4. Update `docs/compatibility.md` and the changelog when discovery paths or resume syntax change.

## Windows installer changes

Changes to `install.ps1`, `run-windows.ps1`, or `uninstall.ps1` must continue to pass PowerShell parser validation and the Windows installation smoke test. The smoke test is expected to install, start, health-check, validate autostart, and uninstall on a clean GitHub-hosted Windows runner.

## Security boundary

The HTTP server listens only on `127.0.0.1`. Resume requests reconstruct commands from validated source/session fields on the server. The Codex visualization endpoint is restricted to raster image files beneath the current user's `~/.codex/visualizations` directory and rejects path traversal.
