"""Host labels and cwd remapping for multi-machine sessions."""

import os
import re

from .config import CURRENT_CWD, LOCAL_HOME, LOCAL_USER


_POSIX_HOME_RE = re.compile(r"^/(?:Users|home)/([^/]+)(?:/(.*))?$")
_WINDOWS_HOME_RE = re.compile(r"^[A-Za-z]:/Users/([^/]+)(?:/(.*))?$", re.IGNORECASE)
_WSL_WINDOWS_HOME_RE = re.compile(
    r"^/mnt/[A-Za-z]/Users/([^/]+)(?:/(.*))?$", re.IGNORECASE
)


def _slash_path(path):
    """Normalize separators for parsing without changing filesystem paths."""
    return (path or "").strip().replace("\\", "/")


def _home_parts(path):
    """Return ``(username, relative_suffix)`` for recognized home paths.

    Supported recorded forms:
      - macOS: /Users/alice/project
      - Linux/WSL home: /home/alice/project
      - Windows: C:/Users/alice/project (backslashes also accepted)
      - Windows drive viewed from WSL: /mnt/c/Users/alice/project
    """
    normalized = _slash_path(path)
    for pattern in (_WINDOWS_HOME_RE, _WSL_WINDOWS_HOME_RE, _POSIX_HOME_RE):
        match = pattern.match(normalized)
        if match:
            return match.group(1), (match.group(2) or "")
    return None


def _is_under(path, root):
    """Compare two path strings separator-insensitively."""
    path_norm = _slash_path(path).rstrip("/")
    root_norm = _slash_path(root).rstrip("/")
    if not path_norm or not root_norm:
        return False

    # Windows drive paths are case-insensitive. Treating all recognized
    # drive-style paths this way also handles sessions serialized with a
    # different drive-letter case.
    if re.match(r"^[A-Za-z]:/", path_norm) or re.match(r"^[A-Za-z]:/", root_norm):
        path_norm = path_norm.casefold()
        root_norm = root_norm.casefold()

    return path_norm == root_norm or path_norm.startswith(root_norm + "/")


def host_for(cwd):
    """Infer a compact host label from a recorded working directory."""
    if not cwd:
        return LOCAL_USER
    if _is_under(cwd, LOCAL_HOME):
        return LOCAL_USER

    parts = _home_parts(cwd)
    if parts:
        username, _ = parts
        return username

    # Drive-root projects such as D:\\AI\\Pyfluent do not contain a user
    # identity. When they are local, LOCAL_USER is the most useful label;
    # for synced foreign records there is no reliable host identity to infer.
    return LOCAL_USER


def resolve_resume_cwd(cwd):
    """Map a recorded session cwd to something usable on this machine.

    Existing paths are preserved verbatim. If a session came from a different
    machine and its cwd lives under a recognized user home, keep the relative
    suffix and transplant it under this machine's LOCAL_HOME. This supports
    macOS, Linux, native Windows, and Windows paths recorded through WSL.
    """
    cwd = (cwd or "").strip()
    if cwd and os.path.isdir(cwd):
        return cwd

    parts = _home_parts(cwd)
    if parts:
        _, suffix = parts
        components = [part for part in suffix.split("/") if part]
        candidate = os.path.join(LOCAL_HOME, *components) if components else LOCAL_HOME
        if os.path.isdir(candidate):
            return candidate

    return CURRENT_CWD
