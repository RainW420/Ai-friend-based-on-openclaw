# Open Source Readiness

This project is local-first and cloud-ready, but the working tree may contain private runtime data. Run the audit before publishing anything to GitHub.

## Release Gates

The project is not public-ready until:

1. `python3 scripts/open_source_audit.py --json` reports zero P0 findings.
2. P1 findings are either removed, replaced with examples, or explicitly moved outside the public tree.
3. The default persona is a demo persona, not a private seeded persona.
4. Runtime logs, restore directories, bundles, memory state, session paths, and local absolute paths are excluded from git.
5. CI can run unit tests without OpenClaw secrets, Weixin login, or live message sending.
6. `python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json` reports `public_ready: true` with zero P0/P1/P2 findings.

## Public Snapshot Workflow

Do not publish the live working tree directly. Generate `/tmp/clawbot-public-snapshot` with `scripts/build_public_snapshot.py`, audit that snapshot, then review its manifest before any GitHub action.

## What Must Stay Private

- API keys, OpenClaw tokens, SecretRef backing files, and `.env` files.
- Weixin login state, account IDs, targets, and message IDs.
- Session logs, message databases, heartbeat logs, dialogue-router logs, and restore directories.
- Private user profile, exam schedule, private memory, and private seeded persona packages.
- Local absolute paths such as `<home>/.openclaw/...` or machine-specific workspace paths.

## What Can Be Public

- Source scripts after audit.
- Plugin source after dependencies and build output are ignored.
- Example config files.
- Demo persona packages that do not contain private user facts.
- Local-first onboarding docs, WSL2 docs, and persona authoring docs.

## Expected Audit Status Today

The current working tree is expected to fail public readiness because it intentionally contains private runtime evidence. This is acceptable for this audit iteration. The next iteration should use the audit output to decide what to replace or move before a public GitHub release.
