#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "MEMORY.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]
SECRET_PATTERNS = [re.compile(r"sk-[A-Za-z0-9_-]{6,}"), re.compile(r"(?i)(api[_ -]?key|token|secret)\s*[:=]\s*\S+")]
FORBIDDEN_PARTS = {".dreams", "session-corpus", "sessions", "node_modules", "dist", ".openclaw"}


@dataclass
class PersonaPackage:
    slug: str
    path: Path
    profile: dict[str, Any]
    files: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_persona(project_root: Path, slug: str) -> PersonaPackage:
    package_path = project_root / "personas" / slug
    profile_path = package_path / "persona.profile.json"
    profile = load_json(profile_path)
    files = list(profile.get("files", REQUIRED_FILES))
    return PersonaPackage(slug=slug, path=package_path, profile=profile, files=files)


def list_personas(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    personas_dir = project_root / "personas"
    results: list[dict[str, Any]] = []
    if not personas_dir.exists():
        return results
    for child in sorted(personas_dir.iterdir()):
        if not child.is_dir():
            continue
        profile_path = child / "persona.profile.json"
        if not profile_path.exists():
            continue
        profile = load_json(profile_path)
        results.append({"slug": child.name, "display_name": profile.get("display_name", child.name), "path": str(child)})
    return results


def has_forbidden_path(path: Path) -> bool:
    return any(part in FORBIDDEN_PARTS for part in path.parts)


def validate_persona(package: PersonaPackage) -> list[str]:
    issues: list[str] = []
    if package.profile.get("schema_version") != 1:
        issues.append("profile schema_version must be 1")
    if package.profile.get("slug") != package.slug:
        issues.append("profile slug must match folder name")
    privacy = package.profile.get("privacy", {})
    if privacy.get("contains_secret_values") is not False:
        issues.append("privacy.contains_secret_values must be false")
    if privacy.get("contains_raw_private_conversations") is not False:
        issues.append("privacy.contains_raw_private_conversations must be false")
    for required in REQUIRED_FILES:
        if required not in package.files:
            issues.append(f"profile files must include {required}")
    for rel in package.files:
        path = package.path / rel
        if has_forbidden_path(Path(rel)):
            issues.append(f"forbidden path in persona file list: {rel}")
        if not path.exists():
            issues.append(f"missing persona file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(f"secret-like content in {rel}")
                break
    return issues


def backup_existing(workspace: Path, files: list[str], backup_root: Path) -> Path | None:
    existing = [workspace / rel for rel in files if (workspace / rel).exists()]
    if not existing:
        return None
    backup_dir = backup_root / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.copy2(path, backup_dir / path.name)
    return backup_dir


def activate_persona(project_root: Path, slug: str, workspace: Path, backup_root: Path | None = None) -> dict[str, Any]:
    package = load_persona(project_root, slug)
    issues = validate_persona(package)
    if issues:
        return {"ok": False, "issues": issues, "activated_files": [], "backup_dir": None}
    workspace.mkdir(parents=True, exist_ok=True)
    backup_root = backup_root or (project_root / "logs" / "persona-backups" / slug)
    backup_dir = backup_existing(workspace, package.files, backup_root)
    activated: list[str] = []
    for rel in package.files:
        src = package.path / rel
        dst = workspace / rel
        shutil.copy2(src, dst)
        activated.append(rel)
    return {"ok": True, "issues": [], "activated_files": activated, "backup_dir": str(backup_dir) if backup_dir else None}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    validate = sub.add_parser("validate")
    validate.add_argument("slug")
    activate = sub.add_parser("activate")
    activate.add_argument("slug")
    activate.add_argument("--workspace", default=str(PROJECT_ROOT / "workspace" / "clawbot"))
    args = parser.parse_args()
    if args.cmd == "list":
        print(json.dumps({"personas": list_personas(PROJECT_ROOT)}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "validate":
        package = load_persona(PROJECT_ROOT, args.slug)
        issues = validate_persona(package)
        print(json.dumps({"slug": args.slug, "ok": not issues, "issues": issues}, ensure_ascii=False, indent=2))
        return 0 if not issues else 1
    if args.cmd == "activate":
        result = activate_persona(PROJECT_ROOT, args.slug, Path(args.workspace))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
