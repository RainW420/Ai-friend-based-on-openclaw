# Heartbeat

The heartbeat runner may propose proactive check-ins, but public installs must begin in dry-run mode.

Rules:

- Never send a real proactive message during setup verification.
- Summarize events with booleans such as `messageIdPresent` rather than raw message IDs.
- Keep candidate text out of status reports unless the user explicitly asks to preview it.
- Respect quiet hours and user-configured cadence.
