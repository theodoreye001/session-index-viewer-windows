import os
import unittest
from unittest.mock import patch

from siv import host


class HostLabelTests(unittest.TestCase):
    def test_windows_home_username(self):
        with patch.object(host, "LOCAL_HOME", r"C:\Users\Theo"), patch.object(
            host, "LOCAL_USER", "Theo"
        ):
            self.assertEqual(host.host_for(r"C:\Users\Alice\work\repo"), "Alice")

    def test_windows_forward_slashes(self):
        with patch.object(host, "LOCAL_HOME", r"C:\Users\Theo"), patch.object(
            host, "LOCAL_USER", "Theo"
        ):
            self.assertEqual(host.host_for("C:/Users/Alice/work/repo"), "Alice")

    def test_posix_home_username(self):
        with patch.object(host, "LOCAL_HOME", "/Users/theo"), patch.object(
            host, "LOCAL_USER", "theo"
        ):
            self.assertEqual(host.host_for("/home/alice/work/repo"), "alice")

    def test_wsl_windows_home_username(self):
        with patch.object(host, "LOCAL_HOME", r"C:\Users\Theo"), patch.object(
            host, "LOCAL_USER", "Theo"
        ):
            self.assertEqual(
                host.host_for("/mnt/c/Users/Alice/work/repo"), "Alice"
            )

    def test_local_drive_root_project_uses_local_user(self):
        with patch.object(host, "LOCAL_HOME", r"C:\Users\Theo"), patch.object(
            host, "LOCAL_USER", "Theo"
        ):
            self.assertEqual(host.host_for(r"D:\AI\Pyfluent"), "Theo")

    def test_local_home_comparison_accepts_separator_and_case_variants(self):
        with patch.object(host, "LOCAL_HOME", r"C:\Users\Theo"), patch.object(
            host, "LOCAL_USER", "Theo"
        ):
            self.assertEqual(host.host_for("c:/users/theo/work/repo"), "Theo")


class ResolveResumeCwdTests(unittest.TestCase):
    def test_existing_path_is_preserved(self):
        recorded = r"D:\AI\Pyfluent"
        with patch("siv.host.os.path.isdir", side_effect=lambda p: p == recorded):
            self.assertEqual(host.resolve_resume_cwd(recorded), recorded)

    def test_windows_foreign_home_maps_relative_suffix_to_local_home(self):
        recorded = r"C:\Users\Alice\work\repo"
        local_home = os.path.join("LOCAL", "Theo")
        expected = os.path.join(local_home, "work", "repo")
        with patch.object(host, "LOCAL_HOME", local_home), patch.object(
            host, "CURRENT_CWD", "CURRENT"
        ), patch("siv.host.os.path.isdir", side_effect=lambda p: p == expected):
            self.assertEqual(host.resolve_resume_cwd(recorded), expected)

    def test_wsl_windows_home_maps_relative_suffix_to_local_home(self):
        recorded = "/mnt/d/Users/Alice/work/repo"
        local_home = os.path.join("LOCAL", "Theo")
        expected = os.path.join(local_home, "work", "repo")
        with patch.object(host, "LOCAL_HOME", local_home), patch.object(
            host, "CURRENT_CWD", "CURRENT"
        ), patch("siv.host.os.path.isdir", side_effect=lambda p: p == expected):
            self.assertEqual(host.resolve_resume_cwd(recorded), expected)

    def test_posix_home_maps_relative_suffix_to_local_home(self):
        recorded = "/Users/alice/work/repo"
        local_home = os.path.join("LOCAL", "Theo")
        expected = os.path.join(local_home, "work", "repo")
        with patch.object(host, "LOCAL_HOME", local_home), patch.object(
            host, "CURRENT_CWD", "CURRENT"
        ), patch("siv.host.os.path.isdir", side_effect=lambda p: p == expected):
            self.assertEqual(host.resolve_resume_cwd(recorded), expected)

    def test_unmapped_drive_root_falls_back_to_current_cwd(self):
        with patch.object(host, "CURRENT_CWD", r"D:\viewer"), patch(
            "siv.host.os.path.isdir", return_value=False
        ):
            self.assertEqual(host.resolve_resume_cwd(r"E:\foreign\repo"), r"D:\viewer")


if __name__ == "__main__":
    unittest.main()
