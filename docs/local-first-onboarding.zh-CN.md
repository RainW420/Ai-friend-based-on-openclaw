# 本地优先安装引导

本指南适用于 macOS 和 Linux 用户。Windows 用户请使用 WSL2，并参考 `docs/windows-wsl2.zh-CN.md`。

## 环境要求

- Python 3
- Node.js 18 或更新版本
- npm
- OpenClaw CLI
- 通过 OpenClaw secrets 配置好的模型 API 密钥

## 检查环境

```bash
python3 scripts/clawbot_doctor.py
python3 scripts/clawbot_doctor.py --json
```

环境检测工具不会输出任何密钥。在你启动 OpenClaw 之前，Gateway 端口显示警告是正常的。

## Persona 流程

```bash
python3 scripts/clawbot_persona.py list
python3 scripts/clawbot_persona.py validate demo
mkdir -p /tmp/clawbot-persona-test
python3 scripts/clawbot_persona.py activate demo --workspace /tmp/clawbot-persona-test
```

只有验证完 persona 并且理解激活操作会把 persona 的 markdown 文件拷贝到 `workspace/clawbot/` 之后，才激活到正式工作区。

## 运行时检查

```bash
openclaw config validate
openclaw secrets audit
python3 scripts/clawbot_runtime_status.py --json
python3 scripts/clawbot_heartbeat_runner.py --now 2026-06-28T21:00:00+08:00
```

引导阶段**不要**加 `--send`。

## 云端就绪导出

```bash
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-runtime.tar.gz --target /tmp/clawbot-restore
```

需要长时在线时，阅读 `docs/cloud-migration.zh-CN.md`。
