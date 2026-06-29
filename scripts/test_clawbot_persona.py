import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import clawbot_persona as persona


REQUIRED_FILES = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "MEMORY.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]


def write_persona(root: Path, slug: str = "sample") -> Path:
    package = root / "personas" / slug
    package.mkdir(parents=True)
    (package / "persona.profile.json").write_text(json.dumps({
        "schema_version": 1,
        "slug": slug,
        "display_name": "Sample",
        "language": "zh-CN",
        "files": REQUIRED_FILES,
        "privacy": {
            "contains_raw_private_conversations": False,
            "contains_secret_values": False,
            "portable": True
        }
    }), encoding="utf-8")
    for name in REQUIRED_FILES:
        (package / name).write_text(f"# {name}\nSample\n", encoding="utf-8")
    return package


class ClawbotPersonaTests(unittest.TestCase):
    def test_validate_accepts_complete_persona(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_persona(root)
            package = persona.load_persona(root, "sample")
            issues = persona.validate_persona(package)
        self.assertEqual(issues, [])

    def test_validate_rejects_secret_like_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package_dir = write_persona(root)
            (package_dir / "MEMORY.md").write_text("api key: sk-nope", encoding="utf-8")
            package = persona.load_persona(root, "sample")
            issues = persona.validate_persona(package)
        self.assertTrue(any("secret-like" in issue for issue in issues))

    def test_activate_backs_up_existing_workspace_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_persona(root)
            workspace = root / "workspace" / "clawbot"
            workspace.mkdir(parents=True)
            (workspace / "SOUL.md").write_text("old soul", encoding="utf-8")
            result = persona.activate_persona(root, "sample", workspace, backup_root=root / "backups")
            self.assertTrue((workspace / "SOUL.md").read_text(encoding="utf-8").startswith("# SOUL.md"))
            self.assertTrue(result["backup_dir"])
            self.assertTrue(Path(result["backup_dir"]).exists())
            self.assertIn("SOUL.md", result["activated_files"])


if __name__ == "__main__":
    unittest.main()
