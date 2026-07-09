"""Devin CLI sessions from the local SQLite database."""

import os
import sqlite3
from datetime import datetime, timezone

from .. import cache
from ..config import DEVIN_DB
from ..text import clean_inline, clean_multiline, clip, usable_user_text


def collect(limit):
    """Query the Devin CLI SQLite database for non-hidden sessions and
    extract conversation snippets directly from the message_nodes table.

    Devin CLI stores session metadata in `sessions` and the full
    conversation in `message_nodes` (one JSON row per chat message).
    ATIF transcript files under transcripts/ are only written when the
    user opts into --export, so relying on them would miss most
    sessions. Reading from the DB instead captures every session.

    Returns a list of entry dicts (same shape as parse_claude/parse_codex).
    Opens read-only so a running devin process is never blocked. If the
    database is absent (devin-cli not installed) or unreadable, returns [].
    """
    if not os.path.isfile(DEVIN_DB):
        return []
    entries = []
    try:
        conn = sqlite3.connect(f"file:{DEVIN_DB}?mode=ro", uri=True)
        sessions = conn.execute(
            "SELECT id, working_directory, title, last_activity_at, "
            "model, created_at "
            "FROM sessions WHERE hidden = 0 "
            "ORDER BY last_activity_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

        # Aggregate token / tool / turn usage per session in one query so
        # we don't add N+1 round-trips. Matches the metrics fields Devin
        # CLI writes on every assistant message (see /session-stats).
        # peak_context_tokens = max(input_tokens) over assistant turns,
        # i.e. the largest context window this session ever occupied.
        usage_by_sid = {}
        if sessions:
            placeholders = ",".join("?" for _ in sessions)
            rows = conn.execute(
                "SELECT session_id, "
                "  SUM(CASE WHEN json_extract(chat_message,'$.metadata.metrics.input_tokens') IS NOT NULL "
                "    THEN json_extract(chat_message,'$.metadata.metrics.input_tokens') ELSE 0 END), "
                "  SUM(CASE WHEN json_extract(chat_message,'$.metadata.metrics.output_tokens') IS NOT NULL "
                "    THEN json_extract(chat_message,'$.metadata.metrics.output_tokens') ELSE 0 END), "
                "  SUM(CASE WHEN json_extract(chat_message,'$.metadata.metrics.cache_read_tokens') IS NOT NULL "
                "    THEN json_extract(chat_message,'$.metadata.metrics.cache_read_tokens') ELSE 0 END), "
                "  SUM(CASE WHEN json_extract(chat_message,'$.metadata.metrics.cache_creation_tokens') IS NOT NULL "
                "    THEN json_extract(chat_message,'$.metadata.metrics.cache_creation_tokens') ELSE 0 END), "
                "  SUM(CASE WHEN json_extract(chat_message,'$.tool_calls') IS NOT NULL "
                "    THEN json_array_length(json_extract(chat_message,'$.tool_calls')) ELSE 0 END), "
                "  SUM(CASE WHEN json_extract(chat_message,'$.role')='user' "
                "    AND json_extract(chat_message,'$.metadata.is_user_input')=1 THEN 1 ELSE 0 END), "
                "  COUNT(*), "
                "  MAX(CASE WHEN json_extract(chat_message,'$.role')='assistant' "
                "    AND json_extract(chat_message,'$.metadata.metrics.input_tokens') IS NOT NULL "
                "    THEN json_extract(chat_message,'$.metadata.metrics.input_tokens') END) "
                f"FROM message_nodes WHERE session_id IN ({placeholders}) "
                "GROUP BY session_id",
                [s[0] for s in sessions],
            ).fetchall()
            for sid, inp, out, cr, cc, tools, turns, msgs, peak in rows:
                usage_by_sid[sid] = {
                    "input_tokens": inp or 0,
                    "output_tokens": out or 0,
                    "cache_read_tokens": cr or 0,
                    "cache_creation_tokens": cc or 0,
                    "tool_calls": tools or 0,
                    "user_turns": turns or 0,
                    "messages": msgs or 0,
                    "peak_context_tokens": peak or 0,
                }

        for sid, cwd, title, last_activity_at, model, created_at in sessions:
            cache_key = f"devin:{sid}"
            hit = cache.get(cache_key)
            if hit and hit[0] == last_activity_at:
                entries.append(hit[1])
                continue

            first_user = ""
            row = conn.execute(
                "SELECT json_extract(chat_message, '$.content') "
                "FROM message_nodes "
                "WHERE session_id = ? "
                "  AND json_extract(chat_message, '$.role') = 'user' "
                "  AND json_extract(chat_message, '$.metadata.is_user_input') = 1 "
                "ORDER BY node_id LIMIT 1",
                (sid,),
            ).fetchone()
            if row and row[0]:
                text = row[0].strip()
                if text and usable_user_text(text):
                    first_user = text

            last_user = ""
            row = conn.execute(
                "SELECT json_extract(chat_message, '$.content') "
                "FROM message_nodes "
                "WHERE session_id = ? "
                "  AND json_extract(chat_message, '$.role') = 'user' "
                "  AND json_extract(chat_message, '$.metadata.is_user_input') = 1 "
                "ORDER BY node_id DESC LIMIT 1",
                (sid,),
            ).fetchone()
            if row and row[0]:
                text = row[0].strip()
                if text and usable_user_text(text):
                    last_user = text

            last_assistant = ""
            row = conn.execute(
                "SELECT json_extract(chat_message, '$.content') "
                "FROM message_nodes "
                "WHERE session_id = ? "
                "  AND json_extract(chat_message, '$.role') = 'assistant' "
                "  AND json_extract(chat_message, '$.content') != '' "
                "ORDER BY node_id DESC LIMIT 1",
                (sid,),
            ).fetchone()
            if row and row[0]:
                last_assistant = row[0].strip()

            if not last_assistant:
                continue  # skip sessions with no agent output yet

            usage = usage_by_sid.get(sid, {})
            # Wall-clock duration between first and last activity. Sessions
            # span idle time too, so this is an upper bound on active work.
            duration_s = max(0, (last_activity_at or 0) - (created_at or 0))
            usage["duration_s"] = duration_s
            usage["model"] = model or ""

            entry = {
                "source": "devin",
                "sort_ts": datetime.fromtimestamp(
                    last_activity_at, tz=timezone.utc
                ).isoformat(),
                "cwd": cwd or "",
                "session_id": sid,
                "title": clip(clean_inline(title or ""), 200),
                "first_user": clip(clean_inline(first_user)),
                "last_user": clip(clean_inline(last_user)),
                "last_assistant": clean_multiline(last_assistant),
                "usage": usage,
            }
            cache.set(cache_key, (last_activity_at, entry))
            entries.append(entry)

        conn.close()
    except sqlite3.Error:
        return []
    return entries
