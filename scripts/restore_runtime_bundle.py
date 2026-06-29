#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any


REQUIRED_RESTORED_PATHS = [
    "MANIFEST.json",
    "config",
    "workspace",
    "plugins/clawbot-readonly",
]


def safe_extract(tar: tarfile.TarFile, target: Path) -> None:
    target_resolved = target.resolve()
    for member in tar.getmembers():
        dest = (target / member.name).resolve()
        if not str(dest).startswith(str(target_resolved)):
            raise RuntimeError(f"unsafe tar member: {member.name}")
    tar.extractall(target)


def load_manifest(restored_root: Path) -> dict[str, Any]:
    manifest_path = restored_root / "MANIFEST.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_restored(restored_root: Path) -> list[str]:
    issues: list[str] = []
    for rel in REQUIRED_RESTORED_PATHS:
        if not (restored_root / rel).exists():
            issues.append(f"missing required restored path: {rel}")
    forbidden_names = ["secrets.json", "auth-profiles.json"]
    for path in restored_root.rglob("*"):
        if path.name in forbidden_names:
            issues.append(f"forbidden file restored: {path.relative_to(restored_root)}")
        if path.suffix in {".sqlite", ".db", ".pyc"}:
            issues.append(f"forbidden generated artifact restored: {path.relative_to(restored_root)}")
        if "node_modules" in path.parts:
            issues.append(f"node_modules restored: {path.relative_to(restored_root)}")
        if ".dreams" in path.parts or "session-corpus" in path.parts:
            issues.append(f"forbidden dream/session content restored: {path.relative_to(restored_root)}")
    return issues


def restore_bundle(bundle: Path, target: Path) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    with tarfile.open(bundle, "r:gz") as tar:
        safe_extract(tar, target)
    restored_root = target / "clawbot-runtime"
    manifest = load_manifest(restored_root)
    issues = validate_restored(restored_root)
    return {
        "target": str(target),
        "restored_root": str(restored_root),
        "manifest_format": manifest.get("format"),
        "file_count": len(manifest.get("files", [])),
        "issues": issues,
        "ok": not issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    result = restore_bundle(Path(args.bundle), Path(args.target))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
