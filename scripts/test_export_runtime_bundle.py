import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cloud_runtime_inventory as inv
import export_runtime_bundle as exp


class ExportRuntimeBundleTests(unittest.TestCase):
    def test_bundle_includes_manifest_and_excludes_node_modules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            root.mkdir()
            (root / "config").mkdir()
            (root / "config" / "clawbot-heartbeat-runner.json").write_text("{}", encoding="utf-8")
            (root / "plugins" / "clawbot-readonly" / "node_modules").mkdir(parents=True)
            (root / "plugins" / "clawbot-readonly" / "node_modules" / "secret.txt").write_text("sk-nope", encoding="utf-8")
            (root / "workspace" / "clawbot" / "memory").mkdir(parents=True)
            (root / "workspace" / "clawbot" / "memory" / "2026-06-28.md").write_text("memory", encoding="utf-8")
            (root / "plugins" / "clawbot-readonly" / "dist").mkdir(parents=True)
            (root / "plugins" / "clawbot-readonly" / "dist" / "index.js").write_text("// built", encoding="utf-8")
            (root / "workspace" / "clawbot" / "memory" / ".dreams" / "session-corpus").mkdir(parents=True)
            (root / "workspace" / "clawbot" / "memory" / ".dreams" / "session-corpus" / "2026-06-06.txt").write_text("chat log", encoding="utf-8")
            (root / "personas" / "sample").mkdir(parents=True)
            (root / "personas" / "sample" / "persona.profile.json").write_text(
                json.dumps({"schema_version": 1, "slug": "sample", "files": ["SOUL.md"], "privacy": {"contains_secret_values": False, "contains_raw_private_conversations": False}}),
                encoding="utf-8",
            )
            (root / "personas" / "sample" / "SOUL.md").write_text("# SOUL\n", encoding="utf-8")
            fake_config = root / "openclaw.json"
            fake_config.write_text(json.dumps({"tools": {"exec": {"mode": "deny"}}}), encoding="utf-8")
            output = Path(td) / "bundle.tar.gz"
            with patch.object(inv, "OPENCLAW_CONFIG", fake_config), patch.object(exp, "PORTABLE_PATHS", ["config", "plugins/clawbot-readonly", "workspace/clawbot", "personas"]):
                manifest = exp.create_bundle(root, output)
            self.assertTrue(output.exists())
            self.assertGreater(len(manifest["files"]), 0)
            with tarfile.open(output, "r:gz") as tar:
                names = tar.getnames()
            self.assertIn("clawbot-runtime/MANIFEST.json", names)
            self.assertIn("clawbot-runtime/config/clawbot-heartbeat-runner.json", names)
            self.assertNotIn("clawbot-runtime/plugins/clawbot-readonly/node_modules/secret.txt", names)
            self.assertNotIn("clawbot-runtime/plugins/clawbot-readonly/dist/index.js", names)
            self.assertNotIn("clawbot-runtime/workspace/clawbot/memory/.dreams/session-corpus/2026-06-06.txt", names)
            self.assertIn("clawbot-runtime/personas/sample/persona.profile.json", names)
            self.assertIn("clawbot-runtime/personas/sample/SOUL.md", names)


if __name__ == "__main__":
    unittest.main()
