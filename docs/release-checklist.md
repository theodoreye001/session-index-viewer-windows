# Release checklist

Use this checklist for tagged releases of the Windows-capable fork.

## Code and documentation

- [ ] `VERSION` contains the intended semantic version.
- [ ] `CHANGELOG.md` has an entry for the release.
- [ ] `README.md`, `README.zh-CN.md`, `SUPPORT.md`, and `docs/windows.md` match current behavior.
- [ ] No temporary migration-step documentation remains in the release branch.

## Automated validation

- [ ] Windows backend test job passes.
- [ ] macOS backend test job passes.
- [ ] Ubuntu backend test job passes.
- [ ] Windows PowerShell parser validation passes.
- [ ] React production build passes.
- [ ] Windows install smoke test passes install, HTTP health check, autostart verification, and uninstall.

## Manual Windows acceptance

- [ ] Viewer opens at `http://127.0.0.1:7333` after installation.
- [ ] At least one native Windows session resumes successfully through Windows Terminal or the `cmd.exe` fallback.
- [ ] Codex visualization images render through the localhost proxy when present.
- [ ] Closing the installation PowerShell window does not stop the background viewer.
- [ ] `uninstall.ps1` removes autostart and stops the viewer.

## Release

- [ ] Merge the release PR into `master`.
- [ ] Tag the merge commit as `v<version>`.
- [ ] Publish GitHub release notes from `docs/release-v<version>.md`.
- [ ] Confirm the release tag's CI checks remain green.
