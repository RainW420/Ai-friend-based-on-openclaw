#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SKIP_DIR_PARTS = {
    ".git",
    ".codex",
    ".agents",
    "__pycache__",
    "node_modules",
    "dist",
}

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".tar",
    ".gz",
    ".zip",
    ".sqlite",
    ".db",
    ".pyc",
}

# Audit-generated files must not be scanned by the audit itself.
SKIP_AUDIT_OUTPUT_NAMES = {
    "OPEN_SOURCE_AUDIT.md",
    "PUBLIC_SNAPSHOT_MANIFEST.json",
}

SKIP_AUDIT_OUTPUT_PATHS = {
    "logs/deploy/clawbot-open-source-audit-final.json",
    "logs/deploy/2026-06-28-open-source-readiness-audit-report.md",
}

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".py",
    ".ts",
    ".js",
    ".mjs",
    ".yml",
    ".yaml",
    ".toml",
    ".service",
    ".timer",
    ".sh",
    ".example",
}

PATH_RULES = [
    ("private-runtime-log", "P1", re.compile(r"(^|/)logs/(heartbeat-runner|dialogue-router|runtime|hook-diag)")),
    ("private-deploy-restore", "P1", re.compile(r"(^|/)logs/deploy/.+restore")),
    ("private-runtime-bundle", "P1", re.compile(r"(^|/)logs/deploy/.+\.(tar\.gz|tgz)$")),
    ("private-workspace-memory", "P1", re.compile(r"(^|/)workspace/(clawbot/)?memory/")),
    ("private-user-profile", "P1", re.compile(r"(^|/)workspace/(USER|MEMORY|exam-schedule)\.md?$|(^|/)workspace/exam-schedule\.json")),
    ("private-seeded-persona", "P1", re.compile(r"(^|/)personas/xihe/")),
    ("generated-dependency", "P2", re.compile(r"(^|/)(node_modules|dist|__pycache__)/")),
]

CONTENT_RULES = [
    ("api-key", "P0", re.compile(r"(?i)\b[A-Z0-9_]*(API[_-]?KEY|TOKEN|SECRET)\b\s*[:=]\s*(sk-|['\"])")),
    ("sk-secret", "P0", re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")),
    ("local-absolute-path", "P1", re.compile(r"/home/[A-Za-z0-9._-]+/[^\s)'\"]+")),
    ("openclaw-session-path", "P1", re.compile(r"\.openclaw/agents/[^/\s]+/sessions/[^\s)'\"]+")),
    ("weixin-account-id", "P1", re.compile(r"\b[0-9a-f]{12,}-im-bot\b")),
    ("weixin-target", "P1", re.compile(r"@im\.wechat\b")),
]

PRIVATE_TERMS_ENV = "CLAWBOT_AUDIT_PRIVATE_TERMS"
PRIVATE_TERMS_PATH = Path("config/open-source-private-terms.local.txt")


def load_private_terms(project_root: Path) -> list[str]:
    terms: list[str] = []
    env_value = os.environ.get(PRIVATE_TERMS_ENV, "")
    for item in env_value.split(","):
        item = item.strip()
        if item:
            terms.append(item)
    local_path = project_root / PRIVATE_TERMS_PATH
    try:
        text = local_path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    for line in text.splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            terms.append(item)
    return sorted(set(terms))


def redact_private_terms(text: str, private_terms: list[str]) -> str:
    for term in private_terms:
        text = text.replace(term, "<private-term>")
    return text


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return True
    if path.name in SKIP_AUDIT_OUTPUT_NAMES:
        return True
    rel_text = path.as_posix()
    if rel_text in SKIP_AUDIT_OUTPUT_PATHS:
        return True
    suffixes = "".join(path.suffixes)
    if suffixes.endswith(".tar.gz"):
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def looks_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if path.name in {".gitignore", "README", "LICENSE", "SECURITY", "CONTRIBUTING"}:
        return True
    return False


def iter_repo_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_root)
        if should_skip(rel):
            continue
        if not looks_text(rel):
            continue
        files.append(path)
    return sorted(files)


def severity_rank(severity: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "OK": 9}.get(severity, 9)


def redact_excerpt(text: str) -> str:
    text = re.sub(r"sk-[A-Za-z0-9_-]{4,}", "<redacted>", text)
    text = re.sub(r"(?i)(API[_-]?KEY|TOKEN|SECRET)(\s*[:=]\s*)\S+", r"\1\2<redacted>", text)
    text = text.replace("\n", "\\n")
    if len(text) > 180:
        return text[:180] + "...<truncated>"
    return text


def classify_path(rel: Path) -> dict[str, Any]:
    rel_text = rel.as_posix()
    findings = []
    for rule, severity, pattern in PATH_RULES:
        if pattern.search(rel_text):
            findings.append({"rule": rule, "severity": severity})
    if not findings:
        return {"severity": "OK", "rules": []}
    worst = sorted(findings, key=lambda item: severity_rank(item["severity"]))[0]["severity"]
    return {"severity": worst, "rules": findings}


def finding(path: Path, rule: str, severity: str, message: str, line: int | None = None, excerpt: str | None = None, private_terms: list[str] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": path.as_posix(),
        "rule": rule,
        "severity": severity,
        "message": message,
    }
    if line is not None:
        item["line"] = line
    if excerpt:
        safe_excerpt = redact_private_terms(excerpt, private_terms or [])
        item["excerpt"] = redact_excerpt(safe_excerpt)
    return item


def scan_file(project_root: Path, path: Path, private_terms: list[str] | None = None) -> list[dict[str, Any]]:
    rel = path.relative_to(project_root)
    results: list[dict[str, Any]] = []
    private_terms = private_terms or []
    path_class = classify_path(rel)
    for rule in path_class["rules"]:
        results.append(finding(rel, rule["rule"], rule["severity"], "Path should not be published without review", private_terms=private_terms))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        results.append(finding(rel, "read-error", "P2", f"Could not read file: {exc}"))
        return results
    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule, severity, pattern in CONTENT_RULES:
            if pattern.search(line):
                results.append(finding(rel, rule, severity, "Content looks unsafe for public GitHub", line_no, line))
        for term in private_terms:
            if term and term in line:
                results.append(finding(rel, "private-term", "P1", "Content contains a local private audit term", line_no, line, private_terms))
    return results


def summarize(findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"P0": 0, "P1": 0, "P2": 0}
    for item in findings:
        sev = item.get("severity", "P2")
        if sev in counts:
            counts[sev] += 1
    return {
        "total_findings": len(findings),
        "counts": counts,
        "public_ready": counts["P0"] == 0 and counts["P1"] == 0,
    }


def build_audit(project_root: Path = PROJECT_ROOT, private_terms: list[str] | None = None) -> dict[str, Any]:
    project_root = project_root.resolve()
    private_terms = private_terms if private_terms is not None else load_private_terms(project_root)
    findings: list[dict[str, Any]] = []
    for path in iter_repo_files(project_root):
        findings.extend(scan_file(project_root, path, private_terms))
    findings.sort(key=lambda item: (severity_rank(item["severity"]), item["path"], item.get("line", 0), item["rule"]))
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": str(project_root),
        "summary": summarize(findings),
        "findings": findings,
        "recommended_private_paths": [
            "logs/",
            "workspace/",
            "personas/xihe/",
            "logs/deploy/*.tar.gz",
            "logs/deploy/*restore*/",
            "plugins/*/node_modules/",
            "plugins/*/dist/",
        ],
        "recommended_public_actions": [
            "Create a sanitized demo persona before publishing.",
            "Replace local absolute paths with documented example values.",
            "Keep runtime logs, bundles, restore directories, and private memory out of git.",
            "Run this audit before every public release.",
        ],
    }


def render_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# Open Source Audit",
        "",
        f"Generated: {audit['generated_at']}",
        f"Project: `{audit['project_root']}`",
        "",
        "## Summary",
        "",
        f"- Public ready: `{str(summary['public_ready']).lower()}`",
        f"- Total findings: {summary['total_findings']}",
        f"- P0: {summary['counts']['P0']}",
        f"- P1: {summary['counts']['P1']}",
        f"- P2: {summary['counts']['P2']}",
        "",
        "## Top Findings",
        "",
    ]
    for item in audit["findings"][:80]:
        line = f"- `{item['severity']}` `{item['rule']}` `{item['path']}`"
        if "line" in item:
            line += f":{item['line']}"
        if item.get("excerpt"):
            line += f" — `{item['excerpt']}`"
        lines.append(line)
    if len(audit["findings"]) > 80:
        lines.append(f"- Additional findings omitted from Markdown: {len(audit['findings']) - 80}")
    lines.extend([
        "",
        "## Recommended Private Paths",
        "",
    ])
    lines.extend([f"- `{path}`" for path in audit["recommended_private_paths"]])
    lines.extend([
        "",
        "## Recommended Public Actions",
        "",
    ])
    lines.extend([f"- {action}" for action in audit["recommended_public_actions"]])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", help="Write Markdown report path")
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Repository or snapshot root to audit")
    parser.add_argument("--private-terms", help="Optional newline-delimited local private term file")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    private_terms = None
    if args.private_terms:
        private_path = Path(args.private_terms)
        private_terms = [
            line.strip()
            for line in private_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    audit = build_audit(root, private_terms=private_terms)
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(audit), encoding="utf-8")
    if args.json or not args.markdown:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["summary"]["public_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
