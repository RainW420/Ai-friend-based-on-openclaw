import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import open_source_audit as audit

secret_value = "sk-" + "super-secret-value"
local_path = "/home/" + "example-user/projects/clawbot/data/a.jsonl"
account_id = "31a36a80321f" + "-im-bot"
private_term = "PRIVATE_SAMPLE_PERSON"


class OpenSourceAuditTests(unittest.TestCase):
    def test_redact_excerpt_masks_secret_like_values(self):
        text = "DEEPSEEK_" + "API_" + "KEY=" + secret_value
        redacted = audit.redact_excerpt(text)
        self.assertNotIn(secret_value.split("-")[1], redacted)
        self.assertIn("<redacted>", redacted)

    def test_path_classification_marks_logs_and_private_persona(self):
        self.assertEqual(audit.classify_path(Path("logs/heartbeat-runner.jsonl"))["severity"], "P1")
        self.assertEqual(audit.classify_path(Path("personas/xihe/MEMORY.md"))["severity"], "P1")
        self.assertEqual(audit.classify_path(Path("plugins/clawbot-readonly/src/index.ts"))["severity"], "OK")

    def test_scan_file_detects_local_path_weixin_and_person_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "sample.md"
            target.write_text(
                "user " + private_term + "\npath " + local_path + "\naccount " + account_id + "\n",
                encoding="utf-8",
            )
            findings = audit.scan_file(root, target, private_terms=[private_term])
        rules = {item["rule"] for item in findings}
        self.assertIn("private-term", rules)
        self.assertIn("local-absolute-path", rules)
        self.assertIn("weixin-account-id", rules)

    def test_build_audit_counts_findings_without_binary_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "plugins" / "clawbot-readonly" / "src").mkdir(parents=True)
            (root / "plugins" / "clawbot-readonly" / "src" / "index.ts").write_text("export {}\n", encoding="utf-8")
            (root / "workspace").mkdir()
            (root / "workspace" / "USER.md").write_text("Name: " + private_term + "\n", encoding="utf-8")
            (root / "bundle.tar.gz").write_bytes(b"\x1f\x8b\x08")
            result = audit.build_audit(root, private_terms=[private_term])
        self.assertGreaterEqual(result["summary"]["total_findings"], 1)
        self.assertNotIn("bundle.tar.gz", json.dumps(result["findings"]))

    def test_build_audit_is_stable_and_excludes_own_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "workspace").mkdir()
            (root / "workspace" / "USER.md").write_text("Name: " + private_term + "\n", encoding="utf-8")
            (root / "OPEN_SOURCE_AUDIT.md").write_text("sk-" + "abcdefgh not-redacted\n", encoding="utf-8")
            (root / "logs" / "deploy").mkdir(parents=True)
            (root / "logs" / "deploy" / "clawbot-open-source-audit-final.json").write_text("sk-" + "12345678\n", encoding="utf-8")
            r1 = audit.build_audit(root)
            r2 = audit.build_audit(root)
        self.assertEqual(r1["summary"]["total_findings"], r2["summary"]["total_findings"])
        paths = {f["path"] for f in r1["findings"]}
        self.assertNotIn("OPEN_SOURCE_AUDIT.md", paths)

    def test_custom_root_clean_snapshot_is_public_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "personas" / "demo").mkdir(parents=True)
            (root / "workspace.example").mkdir()
            (root / "personas" / "demo" / "AGENTS.md").write_text("Demo Companion\n", encoding="utf-8")
            (root / "workspace.example" / "USER.md").write_text("Example User\n", encoding="utf-8")
            result = audit.build_audit(root)
        self.assertTrue(result["summary"]["public_ready"])
        self.assertEqual(result["summary"]["counts"], {"P0": 0, "P1": 0, "P2": 0})

    def test_custom_root_with_private_workspace_is_not_public_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "workspace").mkdir()
            (root / "workspace" / "USER.md").write_text("Name: " + private_term + "\n", encoding="utf-8")
            result = audit.build_audit(root, private_terms=[private_term])
        rules = {item["rule"] for item in result["findings"]}
        self.assertFalse(result["summary"]["public_ready"])
        self.assertIn("private-user-profile", rules)
        self.assertIn("private-term", rules)

    def test_load_private_terms_reads_env_and_local_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir()
            (root / "config" / "open-source-private-terms.local.txt").write_text(
                "# local only\nPRIVATE_FROM_FILE\n",
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"CLAWBOT_AUDIT_PRIVATE_TERMS": "PRIVATE_FROM_ENV"}):
                terms = audit.load_private_terms(root)
        self.assertIn("PRIVATE_FROM_FILE", terms)
        self.assertIn("PRIVATE_FROM_ENV", terms)

    def test_audit_source_does_not_match_its_own_local_path_rule(self):
        findings = audit.scan_file(audit.PROJECT_ROOT, Path(audit.__file__).resolve())
        rules = {item["rule"] for item in findings}
        self.assertNotIn("local-absolute-path", rules)
        self.assertNotIn("private-term", rules)


if __name__ == "__main__":
    unittest.main()
