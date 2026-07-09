"""Host labels and cwd remapping for multi-machine sessions."""

import os

from .config import CURRENT_CWD, HOME_DIR_RE, LOCAL_HOME, LOCAL_USER


def host_for(cwd):
    if not cwd:
        return LOCAL_USER
    if cwd == LOCAL_HOME or cwd.startswith(LOCAL_HOME + "/"):
        return LOCAL_USER
    match = HOME_DIR_RE.match(cwd)
    if match:
        return match.group(1)
    return LOCAL_USER


def resolve_resume_cwd(cwd):
    """Map a recorded session cwd to something usable on this machine."""
    cwd = (cwd or "").strip()
    if cwd and os.path.isdir(cwd):
        return cwd

    match = HOME_DIR_RE.match(cwd)
    if match:
        suffix = cwd[match.end() :].lstrip("/")
        candidate = os.path.join(LOCAL_HOME, suffix) if suffix else LOCAL_HOME
        if os.path.isdir(candidate):
            return candidate

    return CURRENT_CWD
