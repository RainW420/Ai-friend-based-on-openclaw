# 项目架构

本文档面向想了解组件协作方式、贡献代码或自行适配的开发者。

## 架构总览

Clawbot **不是一个独立应用**。它是挂在 OpenClaw 旁边的一个项目，在上面叠加了七个层次：

| 层级 | 入口 | 职责 |
|------|------|------|
| **Persona 系统** | `scripts/clawbot_persona.py` | `personas/` 下的可移植 persona 包。每个 persona 是一组 markdown 文件，定义身份、价值观、记忆规则和工具策略。通过 CLI 激活。 |
| **心跳执行器** | `scripts/clawbot_heartbeat_runner.py` | 外部 Python 脚本，按时间表提议主动问候。默认 dry-run，真正的消息发送需要显式加 `--send` 参数。 |
| **对话路由器** | `scripts/clawbot_dialogue_router.py` | 根据情感状态、最近联系记录和对话上下文，决策每一轮如何回应。 |
| **只读状态工具** | `scripts/clawbot_runtime_status.py`、`plugins/clawbot-readonly/` | 安全地输出运行时摘要，不泄露密钥、消息 ID 或会话内容。插件在 OpenClaw 内注册了一个 `clawbot_status` 工具。 |
| **云端迁移工具包** | `scripts/cloud_runtime_inventory.py`、`scripts/export_runtime_bundle.py`、`scripts/restore_runtime_bundle.py` | 盘点可移植文件、导出安全 tar.gz 包、在临时目录恢复并做烟雾测试。systemd 模板放在 `systemd/cloud/`。 |
| **开源审计** | `scripts/open_source_audit.py` | 扫描工作树中的私有标记（API 密钥、会话路径、真实姓名、账号 ID），生成已脱敏的审计报告。 |
| **公开快照生成器** | `scripts/build_public_snapshot.py` | 只拷贝公开安全的文件到一个干净快照目录。快照审计结果为零 findings——这是生成 GitHub 发布候选的机制。 |

## 依赖链

```
OpenClaw Gateway（外部）
  └── plugins/clawbot-readonly/     ← agent 内状态工具
  └── persona markdown 文件          ← 被 agent prompt 消费
  └── heartbeat-runner.jsonl        ← 被心跳执行器消费

外部脚本（Python）
  ├── clawbot_heartbeat_runner.py   ← 读取 config + session state，写入日志
  ├── clawbot_dialogue_router.py    ← 读取 session + affective state
  ├── clawbot_runtime_status.py     ← 只读快照
  ├── clawbot_doctor.py             ← 环境检测，不依赖 OpenClaw
  ├── clawbot_persona.py            ← persona 管理，不依赖 OpenClaw
  ├── cloud_runtime_inventory.py    ← 读取 config + 文件系统
  ├── export_runtime_bundle.py      ← 读取 allowlist + inventory
  ├── restore_runtime_bundle.py     ← 验证恢复后的 bundle
  ├── open_source_audit.py          ← 扫描文件系统 + 内容
  └── build_public_snapshot.py      ← 拷贝 allowlist 到干净目录

关键数据目录
  ├── workspace/clawbot/            ← 运行时 persona 文件（私有）
  ├── workspace/clawbot/memory/     ← 记忆索引源文件（私有）
  ├── workspace.example/            ← 新用户示例模板（公开）
  ├── personas/demo/                ← 公开 demo persona（公开）
  ├── personas/xihe/                ← 私有种子 persona（私有）
  ├── logs/                         ← 运行时日志和 bundle（私有）
  └── config/                       ← 运行时配置（私有）+ *.example.json（公开）
```

## Persona 系统设计

Persona 是 `personas/<slug>/` 下的一个可移植文件夹。包含八个必需文件：

| 文件 | 用途 |
|------|------|
| `persona.profile.json` | 结构化元数据：slug、版本、隐私声明、文件清单 |
| `AGENTS.md` | 顶层 agent 指令和运行规则 |
| `SOUL.md` | 核心价值观和情感调性 |
| `IDENTITY.md` | 角色、背后故事、边界 |
| `MEMORY.md` | 记忆契约和存储规则 |
| `USER.md` | 用户档案模板 |
| `TOOLS.md` | 工具使用策略 |
| `HEARTBEAT.md` | 主动消息规则 |

CLI（`clawbot_persona.py`）提供三个命令：

- `list` — 列出已安装的所有 persona
- `validate <slug>` — 检查 profile schema、文件完整性和疑似密钥的内容
- `activate <slug> --workspace <path>` — 把 persona 文件拷贝到工作区，对已有文件做备份

激活到正式工作区之前，应先做验证，最好先在临时目录做烟雾测试。

## 云端迁移管线

迁移工具包按三级管线设计，以安全为第一原则：

1. **盘点**（`cloud_runtime_inventory.py`）：扫描项目树，把路径分类为可移植或排除，并从摘要中脱敏密钥引用。
2. **导出**（`export_runtime_bundle.py`）：生成 tar.gz 归档，只包含可移植文件。自动排除 `node_modules/`、`dist/`、`.dreams/`、`session-corpus/`、`.sqlite`、日志文件和密钥路径。
3. **恢复**（`restore_runtime_bundle.py`）：把 bundle 解压到临时目录，验证必需路径存在且没有包含禁止内容。

`systemd/cloud/` 目录提供了云端部署的 service 和 timer 模板。完整的切/退计划在 `docs/cloud-migration.md` 中。

**重要提示：** 迁移工具包已在本地开发和测试通过，但尚未在任何真实的云服务器上执行过迁移。导出/恢复管线通过了全部单元测试和禁止内容扫描，恢复烟雾测试返回 `ok: true`。实际的云端部署仍待验证。

## 开源安全双工具

两个工具共同维护公私有边界：

1. **审计**（`open_source_audit.py`）：按路径规则和内容规则扫描工作树中的每个文本文件（API 密钥、会话路径、账号 ID、绝对路径）。输出 JSON 或脱敏 Markdown。支持自定义根目录和私有词表。
2. **快照**（`build_public_snapshot.py`）：按 allowlist 拷贝文件子集到干净输出目录。allowlist 包含文档、脚本、插件源码、demo persona、示例配置和 systemd 模板。快照目录可被独立审计。

发布门控：快照审计结果为 `public_ready: true` 且 P0/P1/P2 全部为零。

## 测试覆盖

所有公开脚本都有对应的单元测试：

| 脚本 | 测试文件 | 测试数 |
|------|---------|--------|
| `clawbot_doctor.py` | `test_clawbot_doctor.py` | 3 |
| `clawbot_persona.py` | `test_clawbot_persona.py` | 3 |
| `open_source_audit.py` | `test_open_source_audit.py` | 9 |
| `build_public_snapshot.py` | `test_build_public_snapshot.py` | 3 |
| `export_runtime_bundle.py` | `test_export_runtime_bundle.py` | 1 |
| `restore_runtime_bundle.py` | `test_restore_runtime_bundle.py` | 1 |
| `cloud_runtime_inventory.py` | `test_cloud_runtime_inventory.py` | 2 |

插件测试（`plugins/clawbot-readonly/`）：4 个 TypeScript Vitest 用例。

总计：26 个测试，全部通过。
