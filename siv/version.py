"""Release version helper."""

import os

from .config import ROOT

VERSION_FILE = os.path.join(ROOT, "VERSION")


def read_version():
    """Return the release version recorded in the repository root."""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            value = f.read().strip()
    except OSError:
        return "0.0.0+unknown"
    return value or "0.0.0+unknown"


__version__ = read_version()
