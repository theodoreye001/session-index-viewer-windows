"""Build resume shell commands and open them in a macOS terminal."""

import os
import shlex
import subprocess

from .config import TERMINAL_APP
from .host import resolve_resume_cwd


def resume_command(source, session_id, cwd):
    if source == "devin":
        base = f"devin -r {session_id}"
    elif source == "claude":
        base = f"claude --resume {session_id}"
    elif source == "grok":
        base = f"grok --resume {session_id}"
    else:
        base = f"codex resume {session_id}"
    resolved_cwd = resolve_resume_cwd(cwd)
    return f"cd {shlex.quote(resolved_cwd)} && {base}" if resolved_cwd else base


def detect_terminal():
    if TERMINAL_APP != "auto":
        return TERMINAL_APP
    for app in ("Ghostty", "iTerm"):
        if os.path.isdir(f"/Applications/{app}.app"):
            return app
    return "Terminal"


def open_in_terminal(command):
    app = detect_terminal()
    if app == "Ghostty":
        # On macOS the `ghostty` CLI can't launch the app directly; use
        # `open -na` with --args -e. Ghostty's -e expects argv with no
        # shell interpretation, so wrap in `zsh -l -c` to handle `&&`,
        # PATH, and aliases from the user's shell config.
        subprocess.Popen(
            [
                "open",
                "-na",
                "Ghostty.app",
                "--args",
                "-e",
                "zsh",
                "-l",
                "-c",
                command,
            ]
        )
        return

    escaped = command.replace("\\", "\\\\").replace('"', '\\"')
    if app == "iTerm":
        script = (
            'tell application "iTerm"\n'
            "  create window with default profile\n"
            "  tell current session of current window\n"
            f'    write text "{escaped}"\n'
            "  end tell\n"
            "end tell"
        )
    else:
        # Terminal.app — `do script` first creates the window with the
        # command; the leading `activate` from earlier versions spawned an
        # extra empty window before `do script` ran.
        script = (
            'tell application "Terminal"\n'
            f'  do script "{escaped}"\n'
            "  activate\n"
            "end tell"
        )
    subprocess.Popen(["osascript", "-e", script])
