# Clawbot

English version: [README.md](README.md)。

Clawbot 是一个**本地优先的 AI 伴侣运行时**，基于 [OpenClaw](https://docs.openclaw.ai/) 构建。它在你自己的电脑上运行一个有记忆、会主动关心你的 AI 伙伴，只有在你选择时才会考虑搬到云端。

## 它能做什么

- 通过 OpenClaw Gateway 在本地运行伴侣 persona，具备记忆搜索和主动心跳问候。
- 默认保护隐私：对话记录、persona 数据、API 密钥都留在你机器上。
- 附带云端迁移工具包（已开发但未在实际云服务器上测试），供将来需要 24 小时在线时使用。

## 适合谁

- 想完全控制 AI 伴侣运行时、记忆和工具策略的开发者。
- 重视隐私、偏好本地优先软件的人。
- 对构建长期陪伴系统感兴趣的人。

## 快速开始

先跑环境医生。它会检查你的平台、已安装的工具和项目结构——不会输出任何密钥。

```bash
python3 scripts/clawbot_doctor.py
```

完整引导文档：[docs/local-first-onboarding.md](docs/local-first-onboarding.md)。

Windows 用户请看：[docs/windows-wsl2.md](docs/windows-wsl2.md)。

## Persona 系统

Persona 是 `personas/<slug>/` 下的一个可移植文件夹。项目自带一个**公开 demo persona** 供新用户使用，以及一个**私有种子 persona**，已从所有公开快照和迁移包中排除。

```bash
python3 scripts/clawbot_persona.py list
python3 scripts/clawbot_persona.py validate demo
python3 scripts/clawbot_persona.py activate demo --workspace /tmp/test-workspace
```

创建你自己的 persona：[docs/persona-authoring.md](docs/persona-authoring.md)。

想要深入了解 persona 系统、心跳执行器、对话路由器等组件如何协作，请看 **[docs/project-architecture.md](docs/project-architecture.md)**。

## 安全默认值

这些都是强制执行的，不是建议：

- `tools.exec.mode` 为 `"deny"` —— 禁用通用 shell 执行。
- `affectiveState.injectToMainModel` 为 `false` —— 状态可观测但不注入 prompt。
- 密钥值不会出现在任何导出包或状态输出中。
- 原始会话日志、消息数据库、`.dreams/` 和 `session-corpus/` 已从所有导出包和公开快照中排除。
- 心跳执行器的真正消息发送需要显式的 `--send` 参数。

## 公开快照

活的工作树包含私有运行时数据。要生成 GitHub 就绪的发布候选，使用公开快照生成器：

```bash
python3 scripts/build_public_snapshot.py --output /tmp/clawbot-public-snapshot
python3 scripts/open_source_audit.py --root /tmp/clawbot-public-snapshot --json
```

只有当审计报告 `public_ready: true` 且 findings 为零时，快照才算就绪。详见 [docs/public-snapshot.md](docs/public-snapshot.md)。

## 云端迁移（仅工具链）

云端迁移工具包可用于准备可移植的部署包。所有单元测试和禁止内容扫描均已通过，但**尚未在实际云服务器上测试过**。当前状态应视为"工具链就绪，云端部署待验证"。

```bash
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-runtime.tar.gz --target /tmp/clawbot-restore
```

切/退计划见 [docs/cloud-migration.md](docs/cloud-migration.md)。

## 文档索引

| 文档 | 内容 |
|------|------|
| [local-first-onboarding.md](docs/local-first-onboarding.md) | macOS/Linux 安装引导 |
| [windows-wsl2.md](docs/windows-wsl2.md) | Windows WSL2 引导和限制 |
| [persona-authoring.md](docs/persona-authoring.md) | 如何创建、验证和激活 persona |
| [project-architecture.md](docs/project-architecture.md) | 组件架构、依赖链和设计细节 |
| [cloud-migration.md](docs/cloud-migration.md) | 云端切/退计划和烟雾测试 |
| [open-source-readiness.md](docs/open-source-readiness.md) | 发布门控和公私边界 |
| [public-repo-manifest.md](docs/public-repo-manifest.md) | 允许/替换/私有的路径清单 |
| [public-snapshot.md](docs/public-snapshot.md) | 快照生成和验证流程 |

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
