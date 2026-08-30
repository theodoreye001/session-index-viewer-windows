"""Build resume commands and open them in a platform terminal."""

import os
import shlex
import shutil
import subprocess
import sys

from .config import TERMINAL_APP
from .host import resolve_resume_cwd


def resume_args(source, session_id):
    """Return the CLI argv used to resume one session."""
    if source == "devin":
        return ["devin", "-r", session_id]
    if source == "claude":
        return ["claude", "--resume", session_id]
    if source == "grok":
        return ["grok", "--resume", session_id]
    if source == "pi":
        return ["pi", "--session", session_id]
    if source == "copilot":
        return ["copilot", "--resume", session_id]
    if source == "opencode":
        return ["opencode", "--session", session_id]
    return ["codex", "resume", session_id]


def _windows_quote(value):
    """Quote one value for a command copied into cmd.exe."""
    return '"' + str(value).replace('"', '""') + '"'


def resume_command(source, session_id, cwd):
    """Return a human-copyable resume command for the current platform."""
    args = resume_args(source, session_id)
    resolved_cwd = resolve_resume_cwd(cwd)

    if os.name == "nt":
        base = subprocess.list2cmdline(args)
        if resolved_cwd:
            return f"cd /d {_windows_quote(resolved_cwd)} && {base}"
        return base

    base = shlex.join(args)
    if resolved_cwd:
        return f"cd {shlex.quote(resolved_cwd)} && {base}"
    return base


def detect_terminal():
    """Detect the preferred terminal on the current platform."""
    if sys.platform == "win32":
        if TERMINAL_APP != "auto":
            return TERMINAL_APP
        return "WindowsTerminal" if (shutil.which("wt.exe") or shutil.which("wt")) else "cmd"

    if TERMINAL_APP != "auto":
        return TERMINAL_APP
    for app in ("Ghostty", "iTerm"):
        if os.path.isdir(f"/Applications/{app}.app"):
            return app
    return "Terminal"


def _open_windows_terminal(args, cwd):
    terminal = detect_terminal()
    if terminal == "WindowsTerminal":
        wt = shutil.which("wt.exe") or shutil.which("wt") or "wt.exe"
        subprocess.Popen(
            [wt, "-w", "-1", "new-tab", "-d", cwd, "cmd.exe", "/k", *args]
        )
        return

    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(
        ["cmd.exe", "/k", *args],
        cwd=cwd,
        creationflags=creationflags,
    )


def _open_macos_terminal(command):
    app = detect_terminal()
    if app == "Ghostty":
        # Ghostty's -e expects argv with no shell interpretation, so wrap
        # in zsh to preserve shell syntax in the copyable resume command.
        subprocess.Popen(
            [
                "open",
                "-na",
                "Ghostty.app",
                "--args",
                "--window-save-state=never",
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
        script = (
            'tell application "Terminal"\n'
            f'  do script "{escaped}"\n'
            "  activate\n"
            "end tell"
        )
    subprocess.Popen(["osascript", "-e", script])


def open_in_terminal(source, session_id, cwd):
    """Open a fresh terminal window and resume the selected session."""
    resolved_cwd = resolve_resume_cwd(cwd)
    args = resume_args(source, session_id)

    if sys.platform == "win32":
        _open_windows_terminal(args, resolved_cwd)
        return
    if sys.platform == "darwin":
        _open_macos_terminal(resume_command(source, session_id, resolved_cwd))
        return

    raise RuntimeError(f"unsupported platform: {sys.platform}")
