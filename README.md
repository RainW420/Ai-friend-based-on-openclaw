# Clawbot

中文介绍见 [README.zh-CN.md](README.zh-CN.md)。

Clawbot is a **local-first companion runtime** built on [OpenClaw](https://docs.openclaw.ai/). It runs a warm, memory-aware AI companion on your own machine, with no cloud dependency unless you choose to add one.

## What Clawbot Does

- Runs a companion persona locally through the OpenClaw Gateway, with memory search and proactive heartbeat check-ins.
- Keeps everything private by default: your conversation logs, persona data, and API credentials stay on your machine.
- Includes a cloud migration toolkit (developed but not yet tested on a real cloud server) for when you want 24/7 availability.

## Who It's For

- Developers who want full control over their AI companion's runtime, memory, and tool policy.
- People who care about privacy and prefer local-first software.
- Anyone curious about building a long-running companion system.

## Quick Start

Run the environment doctor first. It checks your platform, installed tools, and project layout — no secrets printed.

```bash
python3 scripts/clawbot_doctor.py
```

Read the full guide at **[docs/local-first-onboarding.md](docs/local-first-onboarding.md)**.

For Windows users, see **[docs/windows-wsl2.md](docs/windows-wsl2.md)**.

## Personas

A persona is a portable folder under `personas/<slug>/`. The project ships with a **demo** persona for public use and a **private seeded** persona that is excluded from all public snapshots and bundles.

```bash
python3 scripts/clawbot_persona.py list
python3 scripts/clawbot_persona.py validate demo
python3 scripts/clawbot_persona.py activate demo --workspace /tmp/test-workspace
```

To create your own persona, read **[docs/persona-authoring.md](docs/persona-authoring.md)**.

For a deep dive into how the persona system, heartbeat runner, dialogue router, and other components fit together, see **[docs/project-architecture.md](docs/project-architecture.md)**.

## Safety Defaults

These are enforced, not suggested:

- `tools.exec.mode` is `"deny"` — generic shell execution is disabled.
- `affectiveState.injectToMainModel` is `false` — state is observed, not injected into prompts.
- Secret values are never exported in bundles or status output.
- Raw session logs, message databases, `.dreams/`, and `session-corpus/` are excluded from all export bundles and public snapshots.
- The heartbeat runner requires an explicit `--send` flag for real message delivery.

## Public Snapshot

The live working tree contains private runtime data. To produce a GitHub-ready release candidate, use the public snapshot builder:

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

The snapshot is ready only when the audit reports `public_ready: true` with zero findings. See **[docs/public-snapshot.md](docs/public-snapshot.md)**.

## Cloud Migration (Toolkit Only)

A cloud migration toolkit exists for preparing portable deployment bundles. It has passed all unit tests and forbidden-content scans, but **has not been tested on a real cloud server**. Treat the current state as "tooling ready, cloud deployment pending."

```bash
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-runtime.tar.gz --target /tmp/clawbot-restore
```

See **[docs/cloud-migration.md](docs/cloud-migration.md)** for the planned cutover and rollback procedure.

## Documentation

| Document | What It Covers |
|----------|---------------|
| [local-first-onboarding.md](docs/local-first-onboarding.md) | macOS/Linux setup guide |
| [windows-wsl2.md](docs/windows-wsl2.md) | Windows WSL2 guide and limitations |
| [persona-authoring.md](docs/persona-authoring.md) | How to create, validate, and activate personas |
| [project-architecture.md](docs/project-architecture.md) | Component architecture, dependency chain, and design details |
| [cloud-migration.md](docs/cloud-migration.md) | Cloud cutover, rollback, and smoke tests |
| [open-source-readiness.md](docs/open-source-readiness.md) | Release gates and public/private boundaries |
| [public-repo-manifest.md](docs/public-repo-manifest.md) | Allow/replace/private path manifest |
| [public-snapshot.md](docs/public-snapshot.md) | Snapshot generation and verification workflow |

## License

MIT — see [LICENSE](LICENSE).
