# Public Repository Manifest

This manifest describes the intended public GitHub shape. It is not a deletion plan.

## Public By Default

- `README.md`
- `docs/local-first-onboarding.md`
- `docs/windows-wsl2.md`
- `docs/persona-authoring.md`
- `docs/cloud-migration.md`
- `docs/open-source-readiness.md`
- `docs/public-repo-manifest.md`
- `scripts/clawbot_doctor.py`
- `scripts/clawbot_persona.py`
- `scripts/open_source_audit.py`
- `scripts/export_runtime_bundle.py`
- `scripts/restore_runtime_bundle.py`
- `scripts/cloud_runtime_inventory.py`
- `plugins/clawbot-readonly/src/`
- `plugins/clawbot-readonly/package.json`
- `plugins/clawbot-readonly/openclaw.plugin.json`
- `config/*.example.json`
- `systemd/cloud/`

## Replace Before Public

- `personas/xihe/` -> replace with `personas/demo/`
- `workspace/` -> replace with `workspace.example/`
- `config/clawbot-heartbeat-runner.json` -> replace target/account values with documented example values
- `config/clawbot-dialogue-router.json` -> replace local session paths with documented example values

## Private By Default

- `logs/`
- `workspace/clawbot/memory/`
- `workspace/memory/`
- `workspace/persona-backups/`
- `plugins/*/node_modules/`
- `plugins/*/dist/`
- `*.tar.gz`
- `.env`
- `.openclaw/`

## Public Snapshot Rule

The public GitHub repository should be created from a generated snapshot, not from the live working tree.

Use:

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

The snapshot must include `personas/demo/`, `workspace.example/`, and `config/*.example.json`. It must not include `workspace/`, `personas/xihe/`, `logs/`, runtime bundles, restore directories, account IDs, message targets, or local absolute paths.

## Publication Rule

If a file contains a real person, real account, real local path, real session path, real message target, or runtime evidence that would not help a new user install the project, keep it private or replace it with an example.
