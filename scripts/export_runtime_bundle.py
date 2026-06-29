#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

from cloud_runtime_inventory import PROJECT_ROOT, PORTABLE_PATHS, build_inventory


EXCLUDE_PARTS = {
    "node_modules",
    "dist",
    "__pycache__",
    ".git",
    ".codex",
    ".agents",
    ".openclaw",
    ".dreams",
}

EXCLUDE_NAMES = {
    "package-lock.json",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return False
    if path.name in EXCLUDE_NAMES:
        return False
    if path.suffix in {".pyc", ".sqlite", ".db"}:
        return False
    return True


def iter_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in PORTABLE_PATHS:
        path = project_root / rel
        if not path.exists():
            continue
        if path.is_file():
            if should_include(path.relative_to(project_root)):
                files.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file():
                rel_child = child.relative_to(project_root)
                if should_include(rel_child):
                    files.append(child)
    return sorted(set(files))


def validate_manifest(manifest: dict[str, Any]) -> None:
    serialized = json.dumps({
        "files": manifest.get("files", []),
        "restore_notes": manifest.get("restore_notes", []),
    }, ensure_ascii=False)
    forbidden = ["DEEPSEEK_API_KEY", "sk-", "secrets.json", "auth-profiles", "sessions/", ".dreams", "session-corpus"]
    found = [item for item in forbidden if item in serialized]
    if found:
        raise RuntimeError(f"manifest contains forbidden content: {found}")


def create_bundle(project_root: Path, output: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = iter_files(project_root)
    inventory = build_inventory(project_root)
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": str(project_root),
        "format": "clawbot-cloud-readiness-v1",
        "files": [
            {
                "path": str(path.relative_to(project_root)),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
        "excluded_paths": inventory["excluded_paths"],
        "safety": inventory["safety"],
        "restore_notes": [
            "Extract into /opt/clawbot or another empty target directory.",
            "Recreate OpenClaw secrets manually on the target server.",
            "Run restore smoke test before starting any cloud service.",
        ],
    }
    validate_manifest(manifest)
    with tarfile.open(output, "w:gz") as tar:
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("clawbot-runtime/MANIFEST.json")
        info.size = len(manifest_bytes)
        tar.addfile(info, fileobj=__import__("io").BytesIO(manifest_bytes))
        for path in files:
            arcname = Path("clawbot-runtime") / path.relative_to(project_root)
            tar.add(path, arcname=str(arcname), recursive=False)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output .tar.gz path")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without writing tarball")
    args = parser.parse_args()
    output = Path(args.output)
    if args.dry_run:
        files = iter_files(PROJECT_ROOT)
        manifest = {"files": [str(p.relative_to(PROJECT_ROOT)) for p in files], "count": len(files)}
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    manifest = create_bundle(PROJECT_ROOT, output)
    print(json.dumps({"output": str(output), "files": len(manifest["files"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
