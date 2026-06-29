# Clawbot Cloud Migration Guide

## Purpose

This guide describes how to move the Clawbot runtime to a cloud server later. This readiness iteration does not perform the migration.

## Target Shape

Cloud server runs:
- OpenClaw Gateway on loopback port `18789`
- Weixin channel after manual login
- `clawbot-readonly` plugin
- external heartbeat runner
- memory search with `ollama` + `bge-m3` if the server has enough memory

Local machine remains:
- development and review workspace
- emergency rollback target

## Minimum Server Recommendation

- Minimum trial: 2 vCPU, 2 GiB RAM, 40 GiB disk, 3 Mbps bandwidth
- Recommended: 2 vCPU, 4-8 GiB RAM, 40-80 GiB disk, 3-5 Mbps bandwidth

2 GiB can run basic Gateway and Weixin with DeepSeek API, but it is tight for Ollama and memory indexing.

## Export On Local Machine

```bash
python3 scripts/cloud_runtime_inventory.py --json
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-cloud-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-cloud-runtime.tar.gz --target /tmp/clawbot-cloud-restore
```

## Cloud Bootstrap Outline

Run these manually on the future cloud server after provisioning:

```bash
sudo useradd -m -s /bin/bash clawbot
sudo mkdir -p /opt/clawbot
sudo chown -R clawbot:clawbot /opt/clawbot
```

Copy the bundle to the server, then as user `clawbot`:

```bash
mkdir -p /opt/clawbot
tar -xzf clawbot-cloud-runtime.tar.gz -C /opt/clawbot
cd /opt/clawbot/clawbot-runtime
```

Install Node/OpenClaw using the same major runtime as local. Recreate OpenClaw secrets manually; do not copy `~/.openclaw/secrets.json`.

## Cutover Sequence

1. Keep local OpenClaw Gateway running while cloud is prepared without Weixin login.
2. On cloud, validate config and Gateway loopback.
3. Stop local Gateway before cloud Weixin login.
4. Login Weixin on cloud.
5. Verify one manual private-message round trip.
6. Run heartbeat runner without `--send`.
7. Enable heartbeat timer only after dry-run logs look correct.

## Rollback

If cloud Weixin or Gateway fails:

1. Stop cloud Gateway and heartbeat timer.
2. Start local OpenClaw Gateway.
3. Re-login Weixin locally if required.
4. Confirm `openclaw channels status`.

## Smoke Tests

```bash
openclaw config validate
openclaw secrets audit
openclaw gateway status
openclaw channels status
openclaw memory status --agent clawbot --deep
python3 scripts/clawbot_runtime_status.py --json
python3 scripts/clawbot_heartbeat_runner.py --now 2026-06-28T21:00:00+08:00
```

Do not run heartbeat with `--send` during smoke tests.

## Safety Rules

- Gateway stays loopback-only.
- SSH key login only.
- Cloud firewall exposes SSH only.
- `tools.exec.mode` remains `deny`.
- `affectiveState.injectToMainModel` remains `false`.
- No secret values in exported bundle.
