import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import clawbot_doctor as doctor


class ClawbotDoctorTests(unittest.TestCase):
    def test_detect_platform_marks_wsl2(self):
        with patch.object(doctor.platform, "system", return_value="Linux"), \
             patch.object(doctor.platform, "release", return_value="5.15.90.1-microsoft-standard-WSL2"), \
             patch.object(doctor.platform, "machine", return_value="x86_64"):
            result = doctor.detect_platform()
        self.assertEqual(result["os"], "linux")
        self.assertTrue(result["is_wsl2"])
        self.assertEqual(result["support_tier"], "wsl2-docs")

    def test_probe_command_redacts_output_and_reports_missing(self):
        missing = doctor.probe_command("definitely-not-installed-command")
        self.assertEqual(missing["status"], "missing")
        self.assertNotIn("sk-", json.dumps(missing))

    def test_run_checks_uses_project_files_without_secret_values(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "config").mkdir()
            (root / "workspace" / "clawbot").mkdir(parents=True)
            (root / "personas" / "demo").mkdir(parents=True)
            (root / "personas" / "demo" / "persona.profile.json").write_text(
                json.dumps({"schema_version": 1, "slug": "demo", "display_name": "Demo Companion"}),
                encoding="utf-8",
            )
            with patch.object(doctor, "check_port", return_value={"id": "network.gateway_port", "status": "warn", "host": "127.0.0.1", "port": 18789, "connectable": False}):
                result = doctor.run_checks(root)
        self.assertIn("summary", result)
        self.assertIn("checks", result)
        self.assertTrue(any(check["id"] == "project.config" for check in result["checks"]))
        self.assertNotIn("sk-", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
