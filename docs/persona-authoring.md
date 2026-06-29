# Persona Authoring

A persona is a portable folder under `personas/<slug>/`.

## Required Files

- `persona.profile.json`
- `AGENTS.md`
- `SOUL.md`
- `IDENTITY.md`
- `MEMORY.md`
- `USER.md`
- `TOOLS.md`
- `HEARTBEAT.md`

## Create A New Persona

1. Copy `personas/demo` to `personas/<your-slug>`.
2. Edit `persona.profile.json`.
3. Edit the markdown files.
4. Run `python3 scripts/clawbot_persona.py validate <your-slug>`.
5. Smoke-test activation with `--workspace /tmp/clawbot-persona-test`.

## Borrowed Pattern From Skill-Style Persona Projects

The v0 flow keeps the same conceptual split:

- Profile: structured metadata and privacy declarations.
- Persona: identity, values, speech style, and boundaries.
- Memory: curated long-term facts, not raw chat logs.
- Corrections: not automated in v0; write corrections into the markdown files and keep folder copies for rollback.

## Privacy Rules

Do not place API keys, raw session logs, message databases, `.dreams`, or `session-corpus` inside persona folders.
