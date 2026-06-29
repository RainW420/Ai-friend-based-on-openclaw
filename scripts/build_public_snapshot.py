#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PUBLIC_PATHS = [
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    ".gitignore",
    ".github/workflows/ci.yml",
    "docs/local-first-onboarding.md",
    "docs/local-first-onboarding.zh-CN.md",
    "docs/windows-wsl2.md",
    "docs/windows-wsl2.zh-CN.md",
    "docs/persona-authoring.md",
    "docs/persona-authoring.zh-CN.md",
    "docs/cloud-migration.md",
    "docs/cloud-migration.zh-CN.md",
    "docs/open-source-readiness.md",
    "docs/open-source-readiness.zh-CN.md",
    "docs/public-repo-manifest.md",
    "docs/public-repo-manifest.zh-CN.md",
    "docs/project-architecture.md",
    "docs/project-architecture.zh-CN.md",
    "docs/public-snapshot.md",
    "docs/public-snapshot.zh-CN.md",
    "scripts/clawbot_doctor.py",
    "scripts/clawbot_persona.py",
    "scripts/open_source_audit.py",
    "scripts/build_public_snapshot.py",
    "scripts/export_runtime_bundle.py",
    "scripts/restore_runtime_bundle.py",
    "scripts/cloud_runtime_inventory.py",
    "scripts/test_clawbot_doctor.py",
    "scripts/test_clawbot_persona.py",
    "scripts/test_open_source_audit.py",
    "scripts/test_build_public_snapshot.py",
    "scripts/test_export_runtime_bundle.py",
    "scripts/test_restore_runtime_bundle.py",
    "scripts/test_cloud_runtime_inventory.py",
    "plugins/clawbot-readonly/README.md",
    "plugins/clawbot-readonly/package.json",
    "plugins/clawbot-readonly/package-lock.json",
    "plugins/clawbot-readonly/openclaw.plugin.json",
    "plugins/clawbot-readonly/tsconfig.json",
    "plugins/clawbot-readonly/src",
    "plugins/clawbot-readonly/scripts",
    "config/openclaw.example.json",
    "config/clawbot-heartbeat-runner.example.json",
    "config/clawbot-dialogue-router.example.json",
    "personas/README.md",
    "personas/demo",
    "workspace.example",
    "systemd/cloud",
]

PRIVATE_PREFIXES = [
    "workspace/",
    "personas/xihe/",
    "logs/",
    ".git/",
    ".codex/",
    ".agents/",
    ".openclaw/",
]

EXCLUDE_PARTS = {
    "__pycache__",
    "node_modules",
    "dist",
    ".dreams",
    "session-corpus",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".sqlite",
    ".db",
    ".tar",
    ".gz",
    ".zip",
}


def rel_posix(path: Path) -> str:
    return path.as_posix()


def is_private_rel(rel: Path) -> bool:
    text = rel_posix(rel)
    if any(text == prefix.rstrip("/") or text.startswith(prefix) for prefix in PRIVATE_PREFIXES):
        return True
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return True
    if "".join(rel.suffixes).endswith(".tar.gz"):
        return True
    if rel.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_reset_output(project_root: Path, output_root: Path) -> None:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    if output_root == project_root:
        raise ValueError("output root must not be the project root")
    if output_root in project_root.parents:
        raise ValueError("output root must not be a parent of the project root")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def copy_one(project_root: Path, output_root: Path, rel_text: str) -> list[Path]:
    src = project_root / rel_text
    copied: list[Path] = []
    if not src.exists():
        return copied
    if src.is_file():
        rel = Path(rel_text)
        if is_private_rel(rel):
            return copied
        dest = output_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(dest)
        return copied
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(project_root)
        if is_private_rel(rel):
            continue
        dest = output_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        copied.append(dest)
    return copied


def write_manifest(project_root: Path, output_root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(output_root)
        if rel.name == "PUBLIC_SNAPSHOT_MANIFEST.json":
            continue
        files.append({
            "path": rel_posix(rel),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": "local-working-tree",
        "output_root": ".",
        "file_count": len(files),
        "files": files,
    }
    (output_root / "PUBLIC_SNAPSHOT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_snapshot(project_root: Path, output_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    safe_reset_output(project_root, output_root)
    for rel_text in PUBLIC_PATHS:
        copy_one(project_root, output_root, rel_text)
    return write_manifest(project_root, output_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Directory to create or replace with the sanitized public snapshot")
    args = parser.parse_args()
    manifest = build_snapshot(PROJECT_ROOT, Path(args.output))
    print(json.dumps({
        "ok": True,
        "output_root": manifest["output_root"],
        "file_count": manifest["file_count"],
        "manifest": str(Path(args.output).resolve() / "PUBLIC_SNAPSHOT_MANIFEST.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
