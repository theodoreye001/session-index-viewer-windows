"""Safe localhost proxy helpers for Codex visualization images."""

import os
import re
from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urlparse

CODEX_VISUALIZATIONS_ROOT = os.path.realpath(
    os.path.expanduser("~/.codex/visualizations")
)
MAX_LOCAL_IMAGE_BYTES = 25 * 1024 * 1024

_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}

_FILE_URL_RE = re.compile(r"file:///[^\s)\]<>\"']+", re.IGNORECASE)
_VIS_MARKER = "/.codex/visualizations/"


class LocalMediaError(ValueError):
    """Raised when a requested local-media path is unsafe or unsupported."""


def _rewrite_one_file_url(match):
    raw_url = match.group(0)
    try:
        parsed = urlparse(raw_url)
        path = unquote(parsed.path).replace("\\", "/")
    except ValueError:
        return raw_url

    folded = path.casefold()
    idx = folded.find(_VIS_MARKER)
    if idx < 0:
        return raw_url

    relative = path[idx + len(_VIS_MARKER) :].lstrip("/")
    if not relative:
        return raw_url
    return "/api/codex-visualization?path=" + quote(relative, safe="/")


def rewrite_codex_visualization_urls(text):
    """Rewrite local Codex visualization file URLs to the localhost proxy."""
    if not text or "file:///" not in text.casefold():
        return text
    return _FILE_URL_RE.sub(_rewrite_one_file_url, text)


def resolve_codex_visualization(relative_path):
    """Resolve a safe image path below ~/.codex/visualizations.

    The caller supplies only a relative path. Absolute paths, traversal,
    unsupported file types, missing files, and oversized files are rejected.
    """
    raw = (relative_path or "").strip().replace("\\", "/")
    if not raw or len(raw) > 4096 or "\x00" in raw:
        raise LocalMediaError("invalid visualization path")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise LocalMediaError("absolute paths are not allowed")

    pure = PurePosixPath(raw)
    if any(part == ".." for part in pure.parts):
        raise LocalMediaError("path traversal is not allowed")

    suffix = pure.suffix.casefold()
    content_type = _IMAGE_TYPES.get(suffix)
    if content_type is None:
        raise LocalMediaError("unsupported visualization type")

    root = CODEX_VISUALIZATIONS_ROOT
    candidate = os.path.realpath(os.path.join(root, *pure.parts))
    try:
        common = os.path.commonpath([root, candidate])
    except ValueError as exc:
        raise LocalMediaError("visualization path is outside the allowed root") from exc
    if os.path.normcase(common) != os.path.normcase(root):
        raise LocalMediaError("visualization path is outside the allowed root")

    if not os.path.isfile(candidate):
        raise FileNotFoundError(candidate)
    if os.path.getsize(candidate) > MAX_LOCAL_IMAGE_BYTES:
        raise LocalMediaError("visualization image is too large")

    return candidate, content_type
