import json
import os
import tempfile
import unittest
from unittest.mock import patch

from siv.sources import copilot


def _event(event_type, timestamp, data):
    return {
        "type": event_type,
        "timestamp": timestamp,
        "data": data,
    }


class CopilotEventFallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _write_session(self, sid, events, malformed=False):
        directory = os.path.join(self.root, sid)
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "events.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for index, event in enumerate(events):
                f.write(json.dumps(event) + "\n")
                if malformed and index == 1:
                    f.write('{"type":"assistant.message","data":BROKEN\n')
        return path

    def test_parse_event_log_builds_session_entry(self):
        sid = "019abcde11111111"
        path = self._write_session(
            sid,
            [
                _event(
                    "session.start",
                    "2026-08-29T10:00:00Z",
                    {
                        "sessionId": sid,
                        "model": "gpt-5.6-sol",
                        "context": {"cwd": r"D:\\AI\\CopilotProject"},
                    },
                ),
                _event(
                    "user.message",
                    "2026-08-29T10:00:01Z",
                    {"content": "Inspect this repository"},
                ),
                _event(
                    "tool.execution_start",
                    "2026-08-29T10:00:02Z",
                    {"toolName": "view"},
                ),
                _event(
                    "assistant.message",
                    "2026-08-29T10:00:03Z",
                    {
                        "content": "I found the relevant file.",
                        "model": "gpt-5.6-sol",
                        "outputTokens": 42,
                    },
                ),
                _event(
                    "session.task_complete",
                    "2026-08-29T10:00:04Z",
                    {"summary": "Repository inspection"},
                ),
            ],
        )

        entry = copilot._parse_event_file(path)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["session_id"], sid)
        self.assertEqual(entry["cwd"], r"D:\\AI\\CopilotProject")
        self.assertEqual(entry["first_user"], "Inspect this repository")
        self.assertEqual(entry["last_user"], "Inspect this repository")
        self.assertEqual(entry["last_assistant"], "I found the relevant file.")
        self.assertEqual(entry["title"], "Repository inspection")
        self.assertEqual(entry["usage"]["output_tokens"], 42)
        self.assertEqual(entry["usage"]["tool_calls"], 1)
        self.assertEqual(entry["usage"]["user_turns"], 1)
        self.assertEqual(entry["usage"]["model"], "gpt-5.6-sol")

    def test_malformed_physical_line_does_not_hide_valid_messages(self):
        sid = "019abcde22222222"
        path = self._write_session(
            sid,
            [
                _event(
                    "session.start",
                    "2026-08-29T11:00:00Z",
                    {"sessionId": sid, "context": {"cwd": r"C:\\Work"}},
                ),
                _event(
                    "user.message",
                    "2026-08-29T11:00:01Z",
                    {"content": "Continue"},
                ),
                _event(
                    "assistant.message",
                    "2026-08-29T11:00:03Z",
                    {"content": "Recovered after malformed line."},
                ),
            ],
            malformed=True,
        )

        entry = copilot._parse_event_file(path)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["last_assistant"], "Recovered after malformed line.")

    def test_collect_uses_event_state_when_database_is_missing(self):
        sid = "019abcde33333333"
        self._write_session(
            sid,
            [
                _event(
                    "session.start",
                    "2026-08-29T12:00:00Z",
                    {"sessionId": sid, "context": {"cwd": r"C:\\Repo"}},
                ),
                _event(
                    "user.message",
                    "2026-08-29T12:00:01Z",
                    {"content": "Hello Copilot"},
                ),
                _event(
                    "assistant.message",
                    "2026-08-29T12:00:02Z",
                    {"content": "Hello from the event log."},
                ),
            ],
        )

        missing_db = os.path.join(self.root, "missing.db")
        with (
            patch("siv.sources.copilot.COPILOT_DB", missing_db),
            patch("siv.sources.copilot.COPILOT_SESSION_STATE", self.root),
        ):
            entries = copilot.collect(100)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["session_id"], sid)
        self.assertEqual(entries[0]["last_assistant"], "Hello from the event log.")

    def test_session_without_assistant_text_is_skipped(self):
        sid = "019abcde44444444"
        path = self._write_session(
            sid,
            [
                _event(
                    "session.start",
                    "2026-08-29T13:00:00Z",
                    {"sessionId": sid, "context": {"cwd": r"C:\\Repo"}},
                ),
                _event(
                    "user.message",
                    "2026-08-29T13:00:01Z",
                    {"content": "No answer yet"},
                ),
            ],
        )
        self.assertIsNone(copilot._parse_event_file(path))


if __name__ == "__main__":
    unittest.main()
