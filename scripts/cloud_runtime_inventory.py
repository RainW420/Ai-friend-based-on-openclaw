#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENCLAW_HOME = Path.home() / ".openclaw"
OPENCLAW_CONFIG = OPENCLAW_HOME / "openclaw.json"


PORTABLE_PATHS = [
    "config",
    "workspace/AGENTS.md",
    "workspace/HEARTBEAT.md",
    "workspace/IDENTITY.md",
    "workspace/MEMORY.md",
    "workspace/SOUL.md",
    "workspace/TOOLS.md",
    "workspace/USER.md",
    "workspace/clawbot",
    "workspace/exam-schedule.json",
    "plugins/clawbot-readonly",
    "scripts/clawbot_heartbeat_runner.py",
    "scripts/clawbot_dialogue_router.py",
    "scripts/clawbot_runtime_status.py",
    "scripts/cloud_runtime_inventory.py",
    "scripts/export_runtime_bundle.py",
    "scripts/restore_runtime_bundle.py",
    "scripts/clawbot_doctor.py",
    "scripts/clawbot_persona.py",
    "personas",
    "systemd/cloud",
    "docs/runtime-alignment.md",
    "docs/cloud-migration.md",
    "docs/local-first-onboarding.md",
    "docs/windows-wsl2.md",
    "docs/persona-authoring.md",
]

EXCLUDED_PATHS = [
    "~/.openclaw/secrets.json",
    "~/.openclaw/agents",
    "~/.openclaw/state",
    "~/.openclaw/logs",
    "~/.openclaw/sessions",
    "~/.openclaw/memory",
    "plugins/clawbot-readonly/node_modules",
    "plugins/clawbot-readonly/dist",
    "workspace/clawbot/memory/.dreams",
    "logs/dialogue-router-sync.jsonl",
    "logs/dialogue-router.jsonl",
    "logs/heartbeat-runner.jsonl",
    "logs/runtime",
    "logs/persona-backups",
]


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def exists_info(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    return {
        "path": rel,
        "exists": path.exists(),
        "kind": "dir" if path.is_dir() else "file" if path.is_file() else "missing",
    }


def redact_secret_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: redact_secret_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secret_value(v) for v in value]
    if isinstance(value, str):
        lower = value.lower()
        if lower.startswith("sk-") or "token" in lower or "secret" in lower or len(value) > 80:
            return "<redacted>"
    return value


def collect_secret_refs(config: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []

    def walk(obj: Any, path: list[str]) -> None:
        if isinstance(obj, dict):
            if obj.get("$ref") or obj.get("provider") or obj.get("secret"):
                refs.append({"path": ".".join(path), "value": redact_secret_value(obj)})
            for key, value in obj.items():
                walk(value, path + [str(key)])
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, path + [str(i)])

    walk(config, [])
    return refs


def summarize_openclaw_config() -> dict[str, Any]:
    config = load_json(OPENCLAW_CONFIG, {})
    tools = config.get("tools", {}) if isinstance(config, dict) else {}
    agents = config.get("agents", {}) if isinstance(config, dict) else {}
    defaults = agents.get("defaults", {}) if isinstance(agents, dict) else {}
    plugins = config.get("plugins", {}) if isinstance(config, dict) else {}
    gateway = config.get("gateway", {}) if isinstance(config, dict) else {}
    return {
        "path": str(OPENCLAW_CONFIG),
        "exists": OPENCLAW_CONFIG.exists(),
        "gateway_bind": gateway.get("bind"),
        "gateway_port": gateway.get("port"),
        "tools_profile": tools.get("profile"),
        "exec_mode": (tools.get("exec", {}) or {}).get("mode") if isinstance(tools, dict) else None,
        "also_allow": tools.get("alsoAllow", []) if isinstance(tools, dict) else [],
        "memory_search": defaults.get("memorySearch", {}) if isinstance(defaults, dict) else {},
        "plugin_allow": plugins.get("allow", []) if isinstance(plugins, dict) else [],
        "secret_refs": collect_secret_refs(config if isinstance(config, dict) else {}),
    }


def build_inventory(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    project_root = project_root.resolve()
    openclaw = summarize_openclaw_config()
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": str(project_root),
        "portable_paths": [exists_info(project_root, rel) for rel in PORTABLE_PATHS],
        "excluded_paths": EXCLUDED_PATHS,
        "openclaw": openclaw,
        "safety": {
            "gateway_loopback_required": True,
            "exec_mode_expected": "deny",
            "tools_profile_expected": "messaging",
            "heartbeat_send_forbidden_in_readiness": True,
            "copy_secret_values_forbidden": True,
        },
        "cutover_notes": [
            "Stop local gateway before enabling Weixin on cloud to avoid duplicate channel ownership.",
            "Recreate secrets on cloud manually; do not copy secret values in bundle.",
            "Run heartbeat dry-run on cloud before any real --send.",
            "Keep cloud Gateway loopback-only and use SSH for administration.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()
    inventory = build_inventory(PROJECT_ROOT)
    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print(f"Project: {inventory['project_root']}")
        print(f"Portable paths: {len(inventory['portable_paths'])}")
        print(f"Excluded paths: {len(inventory['excluded_paths'])}")
        print(f"Gateway bind: {inventory['openclaw']['gateway_bind']}")
        print(f"Exec mode: {inventory['openclaw']['exec_mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
