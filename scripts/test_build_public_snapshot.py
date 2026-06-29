import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_public_snapshot as snapshot


class PublicSnapshotBuilderTests(unittest.TestCase):
    def make_project(self, root: Path) -> None:
        (root / "docs").mkdir()
        (root / "scripts").mkdir()
        (root / "config").mkdir()
        (root / "personas" / "demo").mkdir(parents=True)
        (root / "personas" / "xihe").mkdir(parents=True)
        (root / "workspace").mkdir()
        (root / "workspace.example").mkdir()
        (root / "plugins" / "clawbot-readonly" / "src").mkdir(parents=True)
        (root / "plugins" / "clawbot-readonly" / "dist").mkdir(parents=True)
        (root / "logs" / "deploy").mkdir(parents=True)
        (root / "systemd" / "cloud").mkdir(parents=True)

        (root / "README.md").write_text("# Public\n", encoding="utf-8")
        (root / ".gitignore").write_text("logs/\n", encoding="utf-8")
        (root / "docs" / "public-repo-manifest.md").write_text("manifest\n", encoding="utf-8")
        (root / "scripts" / "clawbot_doctor.py").write_text("print('ok')\n", encoding="utf-8")
        (root / "scripts" / "private_helper.py").write_text("PRIVATE_SAMPLE_PERSON\n", encoding="utf-8")
        (root / "config" / "openclaw.example.json").write_text("{}\n", encoding="utf-8")
        (root / "config" / "clawbot-heartbeat-runner.json").write_text("secret\n", encoding="utf-8")
        (root / "personas" / "demo" / "AGENTS.md").write_text("demo\n", encoding="utf-8")
        (root / "personas" / "xihe" / "AGENTS.md").write_text("private\n", encoding="utf-8")
        (root / "workspace" / "USER.md").write_text("private\n", encoding="utf-8")
        (root / "workspace.example" / "USER.md").write_text("Example User\n", encoding="utf-8")
        (root / "plugins" / "clawbot-readonly" / "src" / "index.ts").write_text("export {}\n", encoding="utf-8")
        (root / "plugins" / "clawbot-readonly" / "dist" / "index.js").write_text("built\n", encoding="utf-8")
        (root / "plugins" / "clawbot-readonly" / "package.json").write_text("{\"name\":\"x\"}\n", encoding="utf-8")
        (root / "systemd" / "cloud" / "openclaw-gateway.service").write_text("[Service]\n", encoding="utf-8")
        (root / "logs" / "deploy" / "bundle.tar.gz").write_bytes(b"private")

    def test_build_snapshot_copies_public_allowlist_and_excludes_private_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            out = Path(td) / "snapshot"
            root.mkdir()
            self.make_project(root)
            result = snapshot.build_snapshot(root, out)

            self.assertTrue((out / "README.md").exists())
            self.assertTrue((out / "personas" / "demo" / "AGENTS.md").exists())
            self.assertTrue((out / "workspace.example" / "USER.md").exists())
            self.assertTrue((out / "plugins" / "clawbot-readonly" / "src" / "index.ts").exists())
            self.assertFalse((out / "personas" / "xihe").exists())
            self.assertFalse((out / "workspace").exists())
            self.assertFalse((out / "logs").exists())
            self.assertFalse((out / "plugins" / "clawbot-readonly" / "dist").exists())
            self.assertFalse((out / "config" / "clawbot-heartbeat-runner.json").exists())
            self.assertGreaterEqual(result["file_count"], 1)

    def test_manifest_contains_sha256_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            out = Path(td) / "snapshot"
            root.mkdir()
            self.make_project(root)
            snapshot.build_snapshot(root, out)
            manifest = json.loads((out / "PUBLIC_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))

        paths = {item["path"] for item in manifest["files"]}
        self.assertIn("README.md", paths)
        self.assertIn("personas/demo/AGENTS.md", paths)
        self.assertIn("workspace.example/USER.md", paths)
        self.assertNotIn("personas/xihe/AGENTS.md", paths)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["files"]))

    def test_output_root_must_not_be_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            root.mkdir()
            self.make_project(root)
            with self.assertRaises(ValueError):
                snapshot.build_snapshot(root, root)


if __name__ == "__main__":
    unittest.main()
