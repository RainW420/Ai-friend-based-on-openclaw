# Clawbot Readonly Tools

Fixed read-only OpenClaw tool plugin for the local Clawbot deployment.

The `clawbot_status` tool returns a deployment summary with secrets redacted. It does not expose arbitrary command execution or arbitrary file reads.

## Build

```bash
npm install
npm run plugin:build
npm run plugin:validate
npm test
```
