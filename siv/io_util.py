"""JSONL file reading with optional head+tail windowing."""

import json

from .config import FULL_READ_LIMIT, HEAD_BYTES, TAIL_BYTES


def read_lines(path, size):
    """Return (lines, windowed). Windowed reads cover head + tail only;
    callers must fall back to a full read when fields come up missing."""
    if size <= FULL_READ_LIMIT or HEAD_BYTES + TAIL_BYTES >= size:
        with open(path, "rb") as f:
            data = f.read()
        return data.decode("utf-8", "replace").splitlines(), False

    with open(path, "rb") as f:
        head = f.read(HEAD_BYTES)
        f.seek(size - TAIL_BYTES)
        tail = f.read()

    head_lines = head.decode("utf-8", "replace").splitlines()
    if not head.endswith(b"\n") and head_lines:
        head_lines.pop()  # drop the line cut by the window edge
    tail_text = tail.decode("utf-8", "replace")
    newline = tail_text.find("\n")
    tail_lines = tail_text[newline + 1:].splitlines() if newline != -1 else []
    return head_lines + tail_lines, True


def decode_records(lines):
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records
