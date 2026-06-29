# 公开快照

Clawbot 的工作树可能包含私有运行时数据。不要直接发布它。

请生成脱敏后的公开快照：

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

只有当审计摘要报告以下结果时，快照才算 GitHub 就绪：

- `public_ready: true`
- `P0: 0`
- `P1: 0`
- `P2: 0`

## 包含

- 公开文档
- 公开 Python 辅助脚本及其测试
- `plugins/clawbot-readonly` 源码和包元数据
- `personas/demo`
- `workspace.example`
- `config/*.example.json`
- `systemd/cloud`

## 排除

- `workspace/`
- `personas/xihe/`
- `logs/`
- 运行时 bundle 和恢复目录
- 微信会话、账号 ID、消息目标和消息 ID
- 本地绝对路径
- 依赖和构建产物，如 `node_modules/` 和 `dist/`

## 发布边界

生成的快照是一个发布候选目录。审查 `PUBLIC_SNAPSHOT_MANIFEST.json`，选择一个许可证，仅在独立的人工批准之后才初始化并推送 Git 仓库。
