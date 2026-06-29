# 开源就绪指南

本项目是本地优先的，但工作树中可能包含私有运行时数据。向 GitHub 发布任何内容之前，必须先运行审计。

## 发布门控

满足以下全部条件，项目才算公开发布就绪：

1. `python3 scripts/open_source_audit.py --json` 报告 P0 findings 为零。
2. P1 findings 要么移除，要么替换为示例值，要么显式移出公开目录。
3. 默认 persona 是 demo persona，而非私有种子 persona。
4. 运行时日志、恢复目录、bundle、记忆数据、会话路径和本地绝对路径都已从 git 中排除。
5. CI 可以在没有 OpenClaw secrets、不登录微信、不发送真实消息的前提下跑通单元测试。
6. `python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json` 报告 `public_ready: true` 且 P0/P1/P2 全部为零。

## 公开快照工作流

不要直接发布活的工作树。先用 `scripts/build_public_snapshot.py` 生成 `/tmp/clawbot-public-snapshot`，审计该快照，然后在做任何 GitHub 操作之前审查其 manifest。

## 必须保持私有的内容

- API 密钥、OpenClaw token、SecretRef 后端文件和 `.env` 文件。
- 微信登录状态、账号 ID、消息目标和消息 ID。
- 会话日志、消息数据库、心跳日志、对话路由器日志和恢复目录。
- 私有用户档案、考试日程、私有记忆和私有种子 persona 包。
- 本地绝对路径，比如 `<home>/.openclaw/...` 或机器专属的工作区路径。

## 可以公开的内容

- 经过审计的源代码脚本。
- 排除了依赖和构建产物的插件源码。
- 示例配置文件。
- 不含私有用户事实的 demo persona 包。
- 本地优先引导文档、WSL2 文档和 persona 创作文档。

## 当前审计状态

当前工作树的审计结果预期会不通过，因为它有意包含了私有运行时证据。在本轮审计迭代中这是可接受的。下一轮迭代应利用审计输出，决定哪些内容需要在公开发布前替换或移除。
