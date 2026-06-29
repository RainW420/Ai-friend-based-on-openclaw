# Project Architecture

This document explains the internal structure of Clawbot for developers who want to understand how the pieces fit together, contribute code, or adapt the project for their own use.

## Architecture Overview

Clawbot is **not a standalone application**. It's a project that sits alongside OpenClaw, adding seven layers on top:

| Layer | Entry Point | What It Does |
|-------|-----------|-------------|
| **Persona System** | `scripts/clawbot_persona.py` | Portable persona packages under `personas/`. Each persona is a set of markdown files that define identity, values, memory rules, and tool policy. Activate one with the CLI. |
| **Heartbeat Runner** | `scripts/clawbot_heartbeat_runner.py` | External Python script that proposes proactive check-ins on a schedule. Dry-run by default — real sending requires an explicit `--send` flag. |
| **Dialogue Router** | `scripts/clawbot_dialogue_router.py` | Decides how the companion should respond in each turn using affective state, recency, and conversation context. |
| **Read-Only Status** | `scripts/clawbot_runtime_status.py`, `plugins/clawbot-readonly/` | Exposes safe runtime summaries without leaking secrets, message IDs, or session content. The plugin registers a single `clawbot_status` tool inside OpenClaw. |
| **Cloud Migration Toolkit** | `scripts/cloud_runtime_inventory.py`, `scripts/export_runtime_bundle.py`, `scripts/restore_runtime_bundle.py` | Inventory portable files, export a safe tar.gz bundle, restore into a temp directory for smoke-testing. Systemd templates live in `systemd/cloud/`. |
| **Open Source Audit** | `scripts/open_source_audit.py` | Scans the working tree for private markers (API keys, session paths, personal names, account IDs) and generates a redacted audit report. |
| **Public Snapshot Builder** | `scripts/build_public_snapshot.py` | Copies only public-safe files into a clean snapshot directory. The snapshot audits to zero findings — the mechanism for producing a GitHub release candidate. |

## Dependency Chain

```
OpenClaw Gateway (external)
  └── plugins/clawbot-readonly/     ← in-agent status tool
  └── persona markdown files        ← consumed by agent prompts
  └── heartbeat-runner.jsonl        ← consumed by heartbeat runner

External scripts (Python)
  ├── clawbot_heartbeat_runner.py   ← reads config + session state, writes logs
  ├── clawbot_dialogue_router.py    ← reads session + affective state
  ├── clawbot_runtime_status.py     ← read-only snapshot
  ├── clawbot_doctor.py             ← env check, no OpenClaw dependency
  ├── clawbot_persona.py            ← persona management, no OpenClaw dependency
  ├── cloud_runtime_inventory.py    ← reads config + filesystem
  ├── export_runtime_bundle.py      ← reads allowlist + inventory
  ├── restore_runtime_bundle.py     ← validates restored bundle
  ├── open_source_audit.py          ← scans filesystem + content
  └── build_public_snapshot.py      ← copies allowlist into clean tree

Key data directories
  ├── workspace/clawbot/            ← live runtime persona files (private)
  ├── workspace/clawbot/memory/     ← memory index source (private)
  ├── workspace.example/            ← example template for new users (public)
  ├── personas/demo/                ← public demo persona (public)
  ├── personas/xihe/                ← private seeded persona (private)
  ├── logs/                         ← runtime logs, bundles (private)
  └── config/                       ← runtime config (private) + *.example.json (public)
```

## Persona System Design

A persona is a portable folder under `personas/<slug>/`. It contains eight required files:

| File | Purpose |
|------|---------|
| `persona.profile.json` | Structured metadata: slug, version, privacy declarations, file list |
| `AGENTS.md` | Top-level agent instruction with operating rules |
| `SOUL.md` | Core values and emotional tone |
| `IDENTITY.md` | Role, biography, boundaries |
| `MEMORY.md` | Memory contract and storage rules |
| `USER.md` | User profile template |
| `TOOLS.md` | Tool usage policy |
| `HEARTBEAT.md` | Proactive message rules |

The CLI (`clawbot_persona.py`) provides three commands:

- `list` — enumerate installed personas
- `validate <slug>` — check profile schema, file completeness, and secret-like content
- `activate <slug> --workspace <path>` — copy persona files into a workspace, with backup of existing files

Activation into the live workspace should only be done after validation and, ideally, after smoke-testing in a temporary directory.

## Cloud Migration Pipeline

The migration toolkit follows a three-stage pipeline designed for safety:

1. **Inventory** (`cloud_runtime_inventory.py`): scans the project tree, classifies paths as portable or excluded, and redacts secret references from the summary.
2. **Export** (`export_runtime_bundle.py`): produces a tar.gz archive containing only portable files. Automatically excludes `node_modules/`, `dist/`, `.dreams/`, `session-corpus/`, `.sqlite`, log files, and secret paths.
3. **Restore** (`restore_runtime_bundle.py`): unpacks the bundle into a temporary directory and validates that required paths exist and no forbidden content was included.

A separate `systemd/cloud/` directory provides service and timer templates for cloud deployment. The full cutover and rollback plan is in `docs/cloud-migration.md`.

**Important:** The migration toolkit has been developed and tested locally, but no actual cloud server migration has been performed. The export/restore pipeline passes all unit tests and forbidden-content scans, and the restore smoke test returns `ok: true`. Real-world cloud deployment remains untested.

## Open Source Safety Pipeline

Two tools enforce the public/private boundary:

1. **Audit** (`open_source_audit.py`): scans every text file in the working tree against path rules and content rules (API keys, session paths, account IDs, absolute paths). Outputs JSON or redacted Markdown. Supports custom roots and private term files.
2. **Snapshot** (`build_public_snapshot.py`): copies an allowlisted subset of files into a clean output directory. The allowlist includes docs, scripts, plugin source, demo persona, example configs, and systemd templates. The snapshot directory can then be audited independently.

The release gate: `public_ready: true` with zero P0/P1/P2 findings on a generated snapshot.

## Test Coverage

All public scripts have corresponding unit tests:

| Script | Test File | Tests |
|--------|----------|-------|
| `clawbot_doctor.py` | `test_clawbot_doctor.py` | 3 |
| `clawbot_persona.py` | `test_clawbot_persona.py` | 3 |
| `open_source_audit.py` | `test_open_source_audit.py` | 9 |
| `build_public_snapshot.py` | `test_build_public_snapshot.py` | 3 |
| `export_runtime_bundle.py` | `test_export_runtime_bundle.py` | 1 |
| `restore_runtime_bundle.py` | `test_restore_runtime_bundle.py` | 1 |
| `cloud_runtime_inventory.py` | `test_cloud_runtime_inventory.py` | 2 |

Plugin tests (`plugins/clawbot-readonly/`): 4 TypeScript tests via Vitest.

Total: 26 tests, all passing.
