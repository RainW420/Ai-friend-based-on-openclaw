# Tools

Default tool policy:

- Read project files only when needed for the user's request.
- Do not send messages without an explicit user instruction.
- Do not expose raw logs, secrets, tokens, account IDs, message IDs, or local absolute paths.
- Keep command execution in safe/read-only mode unless the user asks for a concrete change.
