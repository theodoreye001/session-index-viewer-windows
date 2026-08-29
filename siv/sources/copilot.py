"""GitHub Copilot CLI sessions from its DB or durable event logs.

Preferred source: ~/.copilot/session-store.db, which provides a clean relational
view with turns and usage. Fallback source: ~/.copilot/session-state/<id>/events.jsonl,
which is the durable session history used by Copilot CLI resume and is available
on installs where the cross-session DB is missing or incomplete.
"""

import glob
import json
import os
import sqlite3
from datetime import datetime, timezone

from .. import cache
from ..config import COPILOT_DB, COPILOT_SESSION_STATE
from ..text import blocks_text, clean_inline, clean_multiline, clip, usable_user_text


def _collect_db(limit):
    if not os.path.isfile(COPILOT_DB):
        return []
    entries = []
    try:
        conn = sqlite3.connect(f"file:{COPILOT_DB}?mode=ro", uri=True)
        sessions = conn.execute(
            "SELECT id, cwd, summary, created_at, updated_at "
            "FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

        # Aggregate per-turn usage events in one pass. peak_context_tokens
        # = the largest single input_tokens (closest to peak context
        # occupancy); reasoning tokens fold into output like other adapters.
        usage_by_sid = {}
        if sessions:
            placeholders = ",".join("?" for _ in sessions)
            rows = conn.execute(
                "SELECT session_id, "
                "  SUM(COALESCE(input_tokens,0)), "
                "  SUM(COALESCE(output_tokens,0) + COALESCE(reasoning_tokens,0)), "
                "  SUM(COALESCE(cache_read_tokens,0)), "
                "  SUM(COALESCE(cache_write_tokens,0)), "
                "  MAX(COALESCE(input_tokens,0)), "
                "  SUM(COALESCE(duration_ms,0)), "
                "  MAX(model) "
                f"FROM assistant_usage_events WHERE session_id IN ({placeholders}) "
                "GROUP BY session_id",
                [s[0] for s in sessions],
            ).fetchall()
            for sid, inp, out, cr, cw, peak, dur_ms, model in rows:
                usage_by_sid[sid] = {
                    "input_tokens": inp or 0,
                    "output_tokens": out or 0,
                    "cache_read_tokens": cr or 0,
                    "cache_creation_tokens": cw or 0,
                    "tool_calls": 0,
                    "peak_context_tokens": peak or 0,
                    "duration_s": int((dur_ms or 0) / 1000),
                    "model": model or "",
                }

        for sid, cwd, summary, created_at, updated_at in sessions:
            cache_key = f"copilot:{sid}"
            hit = cache.get(cache_key)
            if hit and hit[0] == updated_at:
                if hit[1] is not None:
                    entries.append(hit[1])
                continue

            turns = conn.execute(
                "SELECT user_message, assistant_response FROM turns "
                "WHERE session_id = ? ORDER BY turn_index",
                (sid,),
            ).fetchall()

            first_user = ""
            last_user = ""
            last_assistant = ""
            user_turns = 0
            for user_message, assistant_response in turns:
                if user_message:
                    text = user_message.strip()
                    if text and usable_user_text(text):
                        if not first_user:
                            first_user = text
                        last_user = text
                        user_turns += 1
                if assistant_response and assistant_response.strip():
                    last_assistant = assistant_response.strip()

            if not last_assistant:
                cache.set(cache_key, (updated_at, None))
                continue

            usage = usage_by_sid.get(sid)
            if usage is not None:
                usage["user_turns"] = user_turns
                usage["messages"] = len(turns)

            entry = {
                "source": "copilot",
                "sort_ts": updated_at or created_at or "",
                "cwd": cwd or "",
                "session_id": sid,
                "title": clip(clean_inline(summary or ""), 200),
                "first_user": clip(clean_inline(first_user)),
                "last_user": clip(clean_inline(last_user)),
                "last_assistant": clean_multiline(last_assistant),
                "usage": usage,
            }
            if not entry["sort_ts"]:
                continue
            cache.set(cache_key, (updated_at, entry))
            entries.append(entry)

        conn.close()
    except sqlite3.Error:
        return []
    return entries


def _event_content(data):
    content = (data or {}).get("content")
    return blocks_text(content)


def _parse_event_file(path):
    try:
        stat = os.stat(path)
    except OSError:
        return None

    sid_from_dir = os.path.basename(os.path.dirname(path))
    fingerprint = (stat.st_mtime_ns, stat.st_size)
    cache_key = f"copilot-events:{sid_from_dir}"
    hit = cache.get(cache_key)
    if hit and hit[0] == fingerprint:
        return hit[1]

    session_id = sid_from_dir
    cwd = ""
    title = ""
    first_user = ""
    last_user = ""
    last_assistant = ""
    first_ts = ""
    last_ts = ""
    model = ""
    output_tokens = 0
    tool_calls = 0
    user_turns = 0
    messages = 0

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except (ValueError, TypeError):
                    # Copilot has had versions that can leave a malformed
                    # physical line after interrupted writes. A viewer should
                    # salvage the remaining valid records rather than fail all.
                    continue

                ts = event.get("timestamp") or ""
                if ts:
                    if not first_ts:
                        first_ts = ts
                    last_ts = ts

                etype = event.get("type") or ""
                data = event.get("data") or {}

                if etype == "session.start":
                    session_id = data.get("sessionId") or session_id
                    context = data.get("context") or {}
                    cwd = context.get("cwd") or cwd
                    model = data.get("model") or context.get("model") or model
                elif etype == "session.resume":
                    context = data.get("context") or {}
                    cwd = context.get("cwd") or cwd
                elif etype == "session.model_change":
                    model = data.get("model") or data.get("modelId") or model
                elif etype == "session.task_complete":
                    summary = data.get("summary")
                    if isinstance(summary, str) and summary.strip():
                        title = summary.strip()
                elif etype == "user.message":
                    text = _event_content(data).strip()
                    if text and usable_user_text(text):
                        if not first_user:
                            first_user = text
                        last_user = text
                        user_turns += 1
                        messages += 1
                elif etype == "assistant.message":
                    text = _event_content(data).strip()
                    if text:
                        last_assistant = text
                        messages += 1
                    model = data.get("model") or model
                    try:
                        output_tokens += int(data.get("outputTokens") or 0)
                    except (TypeError, ValueError):
                        pass
                elif etype == "tool.execution_start":
                    tool_calls += 1
    except OSError:
        return None

    if not last_assistant:
        cache.set(cache_key, (fingerprint, None))
        return None

    if not last_ts:
        last_ts = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()

    usage = None
    if output_tokens or tool_calls or user_turns or model:
        duration_s = 0
        if first_ts and last_ts:
            try:
                start = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
                end = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                duration_s = max(0, int((end - start).total_seconds()))
            except ValueError:
                pass
        usage = {
            "input_tokens": 0,
            "output_tokens": output_tokens,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "tool_calls": tool_calls,
            "user_turns": user_turns,
            "messages": messages,
            "peak_context_tokens": 0,
            "duration_s": duration_s,
            "model": model,
        }

    entry = {
        "source": "copilot",
        "sort_ts": last_ts,
        "cwd": cwd,
        "session_id": session_id,
        "title": clip(clean_inline(title), 200),
        "first_user": clip(clean_inline(first_user)),
        "last_user": clip(clean_inline(last_user)),
        "last_assistant": clean_multiline(last_assistant),
        "usage": usage,
    }
    cache.set(cache_key, (fingerprint, entry))
    return entry


def _collect_event_state(limit):
    pattern = os.path.join(COPILOT_SESSION_STATE, "*", "events.jsonl")
    candidates = []
    for path in glob.glob(pattern):
        try:
            candidates.append((os.stat(path).st_mtime, path))
        except OSError:
            continue
    candidates.sort(reverse=True)

    entries = []
    for _, path in candidates[:limit]:
        entry = _parse_event_file(path)
        if entry is not None:
            entries.append(entry)
    return entries


def collect(limit):
    # Keep the relational DB as the preferred fast path. Recent Copilot CLI
    # versions document session-state/events.jsonl as the durable resume data,
    # so use it when the DB is absent, empty, or has an incompatible schema.
    entries = _collect_db(limit)
    if entries:
        return entries
    return _collect_event_state(limit)
