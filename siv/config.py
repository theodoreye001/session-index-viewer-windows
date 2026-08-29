"""Paths, limits, and shared regexes."""

import ntpath
import os
import re
import sys

PORT = 7333
BIND = "127.0.0.1"

# Repo root (parent of the siv package).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAVICON_PATH = os.path.join(ROOT, "favicon.svg")

# Production: serve the built React bundle from frontend/dist/. Dev
# mode uses Vite's dev server (:5173) with a proxy to :7333, so this
# path only matters when running server.py standalone.
DIST_PATH = os.path.join(ROOT, "frontend", "dist")
INDEX_HTML = os.path.join(DIST_PATH, "index.html")
# Fall back to the legacy single-file viewer if the bundle hasn't
# been built yet.
LEGACY_HTML = os.path.join(ROOT, "sessions-index.html")

CLAUDE_GLOB = os.path.expanduser("~/.claude/projects/*/*.jsonl")
CODEX_GLOB = os.path.expanduser("~/.codex/sessions/*/*/*/rollout-*.jsonl")

# Pi agent sessions: ~/.pi/agent/sessions/<encoded-cwd>/<ts>_<uuid>.jsonl.
# Per-file JSONL (session/model_change/message records), so it merges into
# the same mtime-ranked candidate list as Claude/Codex.
PI_GLOB = os.path.expanduser("~/.pi/agent/sessions/*/*.jsonl")


def devin_data_dir(platform=None, env=None, home=None):
    """Return the Devin for Terminal data directory for one platform."""
    platform = platform or sys.platform
    env = os.environ if env is None else env
    home = os.path.expanduser("~") if home is None else home

    override = (env.get("DEVIN_HOME") or "").strip()
    if override:
        return os.path.expanduser(override)

    if platform == "win32":
        roaming = (env.get("APPDATA") or "").strip()
        if not roaming:
            roaming = os.path.join(home, "AppData", "Roaming")
        return os.path.join(roaming, "devin", "cli")
    if platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "devin", "cli")
    return os.path.join(home, ".local", "share", "devin", "cli")


def opencode_db_path(env=None, home=None):
    """Return the OpenCode SQLite path, honoring supported overrides."""
    env = os.environ if env is None else env
    home = os.path.expanduser("~") if home is None else home

    xdg_data = (env.get("XDG_DATA_HOME") or "").strip()
    data_dir = (
        os.path.join(os.path.expanduser(xdg_data), "opencode")
        if xdg_data
        else os.path.join(home, ".local", "share", "opencode")
    )

    override = (env.get("OPENCODE_DB") or "").strip()
    if override:
        override = os.path.expanduser(override)
        if os.path.isabs(override) or ntpath.isabs(override):
            return override
        return os.path.join(data_dir, override)
    return os.path.join(data_dir, "opencode.db")


DEVIN_DATA_DIR = devin_data_dir()
DEVIN_DB = os.path.join(DEVIN_DATA_DIR, "sessions.db")

# GitHub Copilot CLI. session-store.db contains cross-session indexes and
# denormalized turns; session-state/<id>/events.jsonl is the durable session
# history used by resume. The adapter can use the latter when the DB is absent.
COPILOT_DB = os.path.expanduser("~/.copilot/session-store.db")
COPILOT_SESSION_STATE = os.path.expanduser("~/.copilot/session-state")

# OpenCode uses the XDG-style data directory on every platform, including
# Windows. OPENCODE_DB and XDG_DATA_HOME are respected when configured.
OPENCODE_DB = opencode_db_path()

# Grok sessions live under $GROK_HOME/sessions/<encoded-cwd>/<uuid>/
# (default GROK_HOME is ~/.grok). Each session is a directory of JSON/JSONL
# files; summary.json is the index entry and updates.jsonl is the
# authoritative conversation stream used by `grok --resume`.

# Sessions synced across machines keep their recorded cwd. host.py handles
# macOS/Linux homes, native Windows C:\Users\..., and Windows paths viewed
# through WSL (/mnt/c/Users/...). Drive-root project paths that contain no
# username fall back to this machine's LOCAL_USER label.
LOCAL_HOME = os.path.expanduser("~")
LOCAL_USER = os.path.basename(LOCAL_HOME.rstrip("/")) or "unknown"
CURRENT_CWD = os.getcwd() if os.path.isdir(os.getcwd()) else LOCAL_HOME

DEFAULT_LIMIT = 1000
MAX_LIMIT = 1000
CLIP_LEN = 360

# Files larger than this are read head + tail only; smaller ones whole.
FULL_READ_LIMIT = 2 * 1024 * 1024
HEAD_BYTES = 512 * 1024
TAIL_BYTES = 1024 * 1024

# User texts that are harness/CLI noise, not something the human typed.
SKIP_USER_PREFIXES = (
    "Caveat:",
    "<command-",
    "<local-command",
    "<system-reminder",
    "<user-prompt-submit-hook",
    "<environment_context>",
    "<turn_aborted>",
    "<skill-context",
)

SESSION_ID_RE = re.compile(r"^[0-9a-fA-F][0-9a-fA-F-]{6,62}[0-9a-fA-F]$")

# Devin CLI session IDs are memorable word-pair slugs (e.g. "foamy-package").
DEVIN_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,62}$")

# Terminal app to use. "auto" prefers Ghostty > iTerm > Terminal based on
# what's installed. Override by setting to "Ghostty", "iTerm", or "Terminal".
TERMINAL_APP = "auto"

# Sources accepted by POST /api/resume.
RESUME_SOURCES = frozenset(
    {"claude", "codex", "devin", "grok", "pi", "copilot", "opencode"}
)
