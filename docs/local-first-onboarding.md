# Local-First Onboarding

This guide is for macOS and Linux users. Windows users should use WSL2 and follow `docs/windows-wsl2.md`.

## Requirements

- Python 3
- Node.js 18 or newer
- npm
- OpenClaw CLI
- A model provider API key configured through OpenClaw secrets

## Check Your Environment

```bash
python3 scripts/clawbot_doctor.py
python3 scripts/clawbot_doctor.py --json
```

The doctor must not print secret values. A warning is acceptable for the Gateway port before you start OpenClaw locally.

## Persona Flow

```bash
python3 scripts/clawbot_persona.py list
python3 scripts/clawbot_persona.py validate demo
mkdir -p /tmp/clawbot-persona-test
python3 scripts/clawbot_persona.py activate demo --workspace /tmp/clawbot-persona-test
```

Activate into the live workspace only after validating the persona and understanding that activation copies persona markdown files into `workspace/clawbot/`.

## Runtime Checks

```bash
openclaw config validate
openclaw secrets audit
python3 scripts/clawbot_runtime_status.py --json
python3 scripts/clawbot_heartbeat_runner.py --now 2026-06-28T21:00:00+08:00
```

Do not add `--send` during onboarding.

## Cloud-Ready Export

```bash
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-runtime.tar.gz --target /tmp/clawbot-restore
```

Read `docs/cloud-migration.md` when you want long-running cloud availability.
