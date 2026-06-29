#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"


def redact_text(value: str) -> str:
    lowered = value.lower()
    if "sk-" in lowered or "token" in lowered or "secret" in lowered:
        return "<redacted>"
    if len(value) > 500:
        return value[:500] + "...<truncated>"
    return value


def detect_platform() -> dict[str, Any]:
    system = platform.system().lower()
    release = platform.release()
    is_wsl2 = system == "linux" and "microsoft" in release.lower()
    if system == "darwin":
        support_tier = "native-supported"
        os_name = "macos"
    elif system == "linux" and not is_wsl2:
        support_tier = "native-supported"
        os_name = "linux"
    elif is_wsl2:
        support_tier = "wsl2-docs"
        os_name = "linux"
    else:
        support_tier = "unsupported-native"
        os_name = system
    return {
        "os": os_name,
        "raw_system": system,
        "release": release,
        "machine": platform.machine(),
        "is_wsl2": is_wsl2,
        "support_tier": support_tier,
    }


def probe_command(command: str, args: list[str] | None = None) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"id": f"command.{command}", "status": "missing", "command": command}
    cmd = [executable] + (args or ["--version"])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = redact_text((proc.stdout or proc.stderr or "").strip())
        return {
            "id": f"command.{command}",
            "status": "ok" if proc.returncode == 0 else "warn",
            "command": command,
            "path": executable,
            "exit": proc.returncode,
            "output": output,
        }
    except Exception as exc:
        return {"id": f"command.{command}", "status": "warn", "command": command, "path": executable, "error": redact_text(str(exc))}


def check_path(project_root: Path, rel: str, kind: str) -> dict[str, Any]:
    path = project_root / rel
    ok = path.is_dir() if kind == "dir" else path.is_file()
    return {
        "id": f"project.{rel.replace('/', '_')}",
        "status": "ok" if ok else "missing",
        "path": rel,
        "expected": kind,
    }


def check_port(host: str = "127.0.0.1", port: int = 18789) -> dict[str, Any]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError:
        return {"id": "network.gateway_port", "status": "warn", "host": host, "port": port, "connectable": False, "error": "socket-not-available"}
    sock.settimeout(0.25)
    try:
        result = sock.connect_ex((host, port))
        return {"id": "network.gateway_port", "status": "ok" if result == 0 else "warn", "host": host, "port": port, "connectable": result == 0}
    except OSError as exc:
        return {"id": "network.gateway_port", "status": "warn", "host": host, "port": port, "connectable": False, "error": str(exc)}
    finally:
        sock.close()


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"ok": 0, "warn": 0, "missing": 0}
    for check in checks:
        status = check.get("status", "warn")
        counts[status] = counts.get(status, 0) + 1
    ready = counts.get("missing", 0) == 0
    return {"ready": ready, "counts": counts}


def run_checks(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    project_root = project_root.resolve()
    checks: list[dict[str, Any]] = []
    checks.append(check_path(project_root, "config", "dir"))
    checks.append(check_path(project_root, "workspace/clawbot", "dir"))
    checks.append(check_path(project_root, "scripts/clawbot_runtime_status.py", "file"))
    checks.append(check_path(project_root, "personas", "dir"))
    checks.append(check_path(project_root, "personas/demo/persona.profile.json", "file"))
    checks.extend([
        probe_command("node"),
        probe_command("npm"),
        probe_command("python3", ["--version"]),
        probe_command("openclaw", ["--version"]),
    ])
    checks.append(check_port())
    checks.append({
        "id": "openclaw.config_exists",
        "status": "ok" if OPENCLAW_CONFIG.exists() else "warn",
        "path": str(OPENCLAW_CONFIG),
    })
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": str(project_root),
        "platform": detect_platform(),
        "checks": checks,
        "summary": summarize(checks),
        "next_steps": [
            "If native-supported, continue with docs/local-first-onboarding.md.",
            "If wsl2-docs, follow docs/windows-wsl2.md.",
            "Create or activate a persona with scripts/clawbot_persona.py.",
            "Do not paste API keys into reports or persona files.",
        ],
    }


def print_human(result: dict[str, Any]) -> None:
    print("Clawbot Local Doctor")
    print(f"Project: {result['project_root']}")
    print(f"Platform: {result['platform']['os']} ({result['platform']['support_tier']})")
    print(f"Ready: {result['summary']['ready']}")
    for check in result["checks"]:
        print(f"- {check['id']}: {check['status']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_checks(PROJECT_ROOT)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0 if result["summary"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
