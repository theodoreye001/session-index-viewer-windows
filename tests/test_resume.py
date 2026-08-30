import unittest
from unittest.mock import patch

from siv import resume


class ResumeArgsTests(unittest.TestCase):
    def test_codex_args(self):
        self.assertEqual(
            resume.resume_args("codex", "019abcdef123456"),
            ["codex", "resume", "019abcdef123456"],
        )

    def test_claude_args(self):
        self.assertEqual(
            resume.resume_args("claude", "019abcdef123456"),
            ["claude", "--resume", "019abcdef123456"],
        )

    def test_pi_args(self):
        self.assertEqual(
            resume.resume_args("pi", "019abcdef123456"),
            ["pi", "--session", "019abcdef123456"],
        )


class WindowsResumeTests(unittest.TestCase):
    @patch("siv.resume.resolve_resume_cwd", return_value=r"C:\Users\Theo\My Project")
    def test_copyable_windows_command(self, _resolve):
        with patch("siv.resume.os.name", "nt"):
            command = resume.resume_command("codex", "019abcdef123456", "ignored")
        self.assertEqual(
            command,
            'cd /d "C:\\Users\\Theo\\My Project" && codex resume 019abcdef123456',
        )

    @patch("siv.resume.subprocess.Popen")
    @patch("siv.resume.shutil.which")
    @patch("siv.resume.resolve_resume_cwd", return_value=r"D:\AI\Pyfluent")
    def test_windows_terminal_launch(self, _resolve, which, popen):
        which.side_effect = lambda name: r"C:\Windows\wt.exe" if name == "wt.exe" else None
        with patch("siv.resume.sys.platform", "win32"):
            resume.open_in_terminal("codex", "019abcdef123456", "ignored")
        popen.assert_called_once_with(
            [
                r"C:\Windows\wt.exe",
                "-w",
                "-1",
                "new-tab",
                "-d",
                r"D:\AI\Pyfluent",
                "cmd.exe",
                "/k",
                "codex",
                "resume",
                "019abcdef123456",
            ]
        )

    @patch("siv.resume.subprocess.Popen")
    @patch("siv.resume.resolve_resume_cwd", return_value=r"D:\AI\Pyfluent")
    def test_cmd_fallback(self, _resolve, popen):
        with (
            patch("siv.resume.sys.platform", "win32"),
            patch("siv.resume.detect_terminal", return_value="cmd"),
        ):
            resume.open_in_terminal("claude", "019abcdef123456", "ignored")
        popen.assert_called_once()
        args, kwargs = popen.call_args
        self.assertEqual(
            args[0],
            ["cmd.exe", "/k", "claude", "--resume", "019abcdef123456"],
        )
        self.assertEqual(kwargs["cwd"], r"D:\AI\Pyfluent")


if __name__ == "__main__":
    unittest.main()
