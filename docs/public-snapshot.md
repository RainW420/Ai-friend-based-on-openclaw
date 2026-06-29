# Public Snapshot

The live Clawbot working tree may contain private runtime data. Do not publish the live working tree directly.

Generate a sanitized public snapshot instead:

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

The snapshot is GitHub-ready only when the audit summary reports:

- `public_ready: true`
- `P0: 0`
- `P1: 0`
- `P2: 0`

## Included

- Public documentation
- Public Python helper scripts and tests
- `plugins/clawbot-readonly` source and package metadata
- `personas/demo`
- `workspace.example`
- `config/*.example.json`
- `systemd/cloud`

## Excluded

- `workspace/`
- `personas/xihe/`
- `logs/`
- Runtime bundles and restore directories
- Weixin sessions, account IDs, targets, and message IDs
- Local absolute paths
- Dependencies and build output such as `node_modules/` and `dist/`

## Publication Boundary

The generated snapshot is a release candidate tree. Review `PUBLIC_SNAPSHOT_MANIFEST.json`, choose a license, and initialize/push a Git repository only after a separate human approval.
