"""Shared JSONL path scanning + mtime cache for Claude / Codex files."""

import glob
import os

from .. import cache
from ..io_util import decode_records, read_lines
from ..text import clean_inline, clean_multiline, clip


def parse_file(path, parser, size):
    lines, windowed = read_lines(path, size)
    entry = parser(decode_records(lines))
    if windowed:
        # Head+tail can miss middle turns (usage sums, tool counts, and
        # sometimes first/last user). Re-read fully for accurate aggregates.
        with open(path, "rb") as f:
            lines = f.read().decode("utf-8", "replace").splitlines()
        entry = parser(decode_records(lines))
    if entry is None:
        return None
    entry["title"] = clip(clean_inline(entry["title"]), 200)
    entry["first_user"] = clip(clean_inline(entry["first_user"]))
    entry["last_user"] = clip(clean_inline(entry["last_user"]))
    entry["last_assistant"] = clean_multiline(entry["last_assistant"])
    return entry


def cached_entry(path, parser):
    try:
        st = os.stat(path)
    except OSError:
        return None
    hit = cache.get(path)
    if hit and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
        return hit[2]
    try:
        entry = parse_file(path, parser, st.st_size)
    except OSError:
        entry = None
    cache.set(path, (st.st_mtime_ns, st.st_size, entry))
    return entry


def collect_jsonl(pattern, source, parser, limit):
    """Glob session files, parse newest first, return up to `limit` entries.

    Dedup by session_id is left to scan_sessions (syncthing conflict copies
    can share an id across paths).
    """
    candidates = []
    for path in glob.glob(pattern):
        try:
            candidates.append((os.stat(path).st_mtime, path))
        except OSError:
            continue
    candidates.sort(reverse=True)

    entries = []
    for _, path in candidates[:limit]:
        entry = cached_entry(path, parser)
        if entry is None:
            continue
        # Defensive: ensure source matches the collector.
        entry.setdefault("source", source)
        entries.append(entry)
    return entries
