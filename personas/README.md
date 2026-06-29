# Clawbot Personas

A persona package is a portable set of markdown instructions and a small JSON profile.

## Public Demo Persona

`personas/demo/` is the only persona package intended for a public GitHub snapshot. It contains no private user facts, no runtime logs, no account identifiers, and no message targets.

`personas/xihe/` is a private seeded persona and must not be copied into public snapshots.

## Required Files

- `persona.profile.json`
- `AGENTS.md`
- `SOUL.md`
- `IDENTITY.md`
- `MEMORY.md`
- `USER.md`
- `TOOLS.md`
- `HEARTBEAT.md`

## Privacy Rules

Persona packages must not contain API keys, OpenClaw tokens, Weixin login state, raw session logs, message databases, `.dreams`, or `session-corpus`.

## Local-First Workflow

1. Create a folder under `personas/<slug>/`.
2. Write `persona.profile.json`.
3. Edit the markdown files.
4. Run `python3 scripts/clawbot_persona.py validate <slug>`.
5. Run `python3 scripts/clawbot_persona.py activate <slug>` when ready.

## Versioning

For v0, version personas by copying the folder before major edits. Future iterations can add automatic snapshots and rollback.
