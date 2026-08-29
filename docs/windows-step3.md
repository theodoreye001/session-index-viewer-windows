# Windows Step 3 validation

Step 3 adds cross-platform cwd parsing and host labels for native Windows, macOS/Linux, and WSL-recorded paths.

## Supported recorded cwd forms

- `C:\Users\Alice\work\repo`
- `C:/Users/Alice/work/repo`
- `D:\AI\Pyfluent` when the path exists locally
- `/Users/alice/work/repo`
- `/home/alice/work/repo`
- `/mnt/c/Users/Alice/work/repo`

For paths under a recognized user home, a missing foreign-machine path is remapped by keeping its relative suffix and placing that suffix under the current machine's home directory.

Example:

```text
recorded: C:\Users\Alice\work\repo
local:    C:\Users\Theo\work\repo
```

If the local candidate exists, Resume uses it.

Drive-root projects such as `D:\AI\Pyfluent` contain no username. Existing local paths are preserved. Missing foreign drive-root paths cannot be mapped reliably and fall back to the viewer's current working directory.

## Tests

Run:

```powershell
py -m unittest discover -s tests -v
```

Expected after Step 3:

```text
Ran 17 tests
OK
```

## Manual checks

1. Refresh `http://127.0.0.1:7333`.
2. Confirm sessions under `C:\Users\...` render with the expected host username.
3. Confirm a session whose cwd is on `D:\...` still resumes in that exact directory when it exists locally.
4. If WSL-recorded sessions are present, confirm `/mnt/c/Users/...` entries show the embedded Windows username.
5. Re-test one Codex Resume to confirm Windows Terminal still opens and restores the session.

The `file:///C:/...` visualization-image browser restriction is intentionally outside Step 3 and remains a separate local-file serving task.
