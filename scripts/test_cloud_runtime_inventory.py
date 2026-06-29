import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cloud_runtime_inventory as inv


class CloudRuntimeInventoryTests(unittest.TestCase):
    def test_redacts_secret_values(self):
        data = {
            "gateway": {"auth": {"token": "sk-" + "super-secret-value"}},
            "nested": ["normal", "x" * 100],
        }
        redacted = inv.redact_secret_value(data)
        self.assertEqual(redacted["gateway"]["auth"]["token"], "<redacted>")
        self.assertEqual(redacted["nested"][1], "<redacted>")
        self.assertEqual(redacted["nested"][0], "normal")

    def test_build_inventory_classifies_paths_and_constraints(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir()
            (root / "workspace" / "clawbot").mkdir(parents=True)
            (root / "workspace" / "AGENTS.md").write_text("agent", encoding="utf-8")
            fake_config = root / "openclaw.json"
            fake_config.write_text(json.dumps({
                "gateway": {"bind": "loopback", "port": 18789},
                "tools": {"profile": "messaging", "alsoAllow": ["clawbot_status"], "exec": {"mode": "deny"}},
                "agents": {"defaults": {"memorySearch": {"provider": "ollama", "model": "bge-m3"}}},
                "plugins": {"allow": ["clawbot-readonly"]},
            }), encoding="utf-8")
            with patch.object(inv, "OPENCLAW_CONFIG", fake_config):
                result = inv.build_inventory(root)
            self.assertTrue(result["safety"]["gateway_loopback_required"])
            self.assertEqual(result["openclaw"]["exec_mode"], "deny")
            self.assertTrue(any(p["path"] == "config" and p["exists"] for p in result["portable_paths"]))
            self.assertIn("~/.openclaw/secrets.json", result["excluded_paths"])


if __name__ == "__main__":
    unittest.main()
