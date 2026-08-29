import ntpath
import os
import unittest

from siv.config import devin_data_dir, opencode_db_path


class DevinPathTests(unittest.TestCase):
    def test_windows_uses_appdata(self):
        env = {"APPDATA": r"C:\Users\Theo\AppData\Roaming"}
        self.assertEqual(
            devin_data_dir(
                platform="win32",
                env=env,
                home=r"C:\Users\Theo",
            ),
            r"C:\Users\Theo\AppData\Roaming\devin\cli",
        )

    def test_windows_falls_back_to_roaming_under_home(self):
        self.assertEqual(
            devin_data_dir(
                platform="win32",
                env={},
                home=r"C:\Users\Theo",
            ),
            ntpath.join(r"C:\Users\Theo", "AppData", "Roaming", "devin", "cli"),
        )

    def test_macos_application_support(self):
        self.assertEqual(
            devin_data_dir(platform="darwin", env={}, home="/Users/theo"),
            "/Users/theo/Library/Application Support/devin/cli",
        )

    def test_linux_xdg_default(self):
        self.assertEqual(
            devin_data_dir(platform="linux", env={}, home="/home/theo"),
            "/home/theo/.local/share/devin/cli",
        )

    def test_devin_home_override_wins(self):
        self.assertEqual(
            devin_data_dir(
                platform="win32",
                env={"DEVIN_HOME": r"D:\DevinData"},
                home=r"C:\Users\Theo",
            ),
            r"D:\DevinData",
        )


class OpenCodePathTests(unittest.TestCase):
    def test_default_db_below_local_share(self):
        path = opencode_db_path(env={}, home="/home/theo")
        self.assertEqual(path.replace("\\", "/"), "/home/theo/.local/share/opencode/opencode.db")

    def test_absolute_windows_override(self):
        path = opencode_db_path(
            env={"OPENCODE_DB": r"D:\OpenCode\custom.db"},
            home="/home/theo",
        )
        self.assertEqual(path, r"D:\OpenCode\custom.db")

    def test_relative_override_is_below_data_dir(self):
        path = opencode_db_path(
            env={"OPENCODE_DB": "worker.db"},
            home="/home/theo",
        )
        self.assertEqual(path.replace("\\", "/"), "/home/theo/.local/share/opencode/worker.db")

    def test_xdg_data_home_override(self):
        path = opencode_db_path(
            env={"XDG_DATA_HOME": "/data"},
            home="/home/theo",
        )
        self.assertEqual(path.replace("\\", "/"), "/data/opencode/opencode.db")


if __name__ == "__main__":
    unittest.main()
