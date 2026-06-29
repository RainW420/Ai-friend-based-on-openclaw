# 公开仓库清单

这份清单描述的是未来公开 GitHub 仓库的预期形态。它不是删除计划。

## 默认为公开

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

## 发布前需替换

- `personas/xihe/` → 替换为 `personas/demo/`
- `workspace/` → 替换为 `workspace.example/`
- `config/clawbot-heartbeat-runner.json` → 把 target/account 值替换为文档示例值
- `config/clawbot-dialogue-router.json` → 把本地会话路径替换为文档示例值

## 默认为私有

- `logs/`
- `workspace/clawbot/memory/`
- `workspace/memory/`
- `workspace/persona-backups/`
- `plugins/*/node_modules/`
- `plugins/*/dist/`
- `*.tar.gz`
- `.env`
- `.openclaw/`

## 公开快照规则

公开的 GitHub 仓库应从生成快照创建，而非直接从活的工作树创建。

使用：

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

快照必须包含 `personas/demo/`、`workspace.example/` 和 `config/*.example.json`。不得包含 `workspace/`、`personas/xihe/`、`logs/`、运行时 bundle、恢复目录、账号 ID、消息目标或本地绝对路径。

## 发布原则

如果某个文件包含真实姓名、真实账号、真实本地路径、真实会话路径、真实消息目标，或者包含对新用户安装项目没有帮助的运行时数据，请将其保持私有或替换为示例。
