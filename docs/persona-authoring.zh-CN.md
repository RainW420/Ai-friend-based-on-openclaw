# Persona 创作指南

Persona 是 `personas/<slug>/` 下的一个可移植文件夹。

## 必需文件

- `persona.profile.json`
- `AGENTS.md`
- `SOUL.md`
- `IDENTITY.md`
- `MEMORY.md`
- `USER.md`
- `TOOLS.md`
- `HEARTBEAT.md`

## 创建新的 Persona

1. 复制 `personas/demo` 为 `personas/<你的-slug>`。
2. 编辑 `persona.profile.json`。
3. 编辑各 markdown 文件。
4. 运行 `python3 scripts/clawbot_persona.py validate <你的-slug>`。
5. 用 `--workspace /tmp/clawbot-persona-test` 做烟雾测试激活。

## 借鉴技能式 Persona 项目的模式

v0 阶段沿用相同的概念拆分：

- Profile：结构化元数据和隐私声明。
- Persona：身份、价值观、说话风格和边界。
- Memory：精选的长期记忆，而非原始聊天记录。
- 修正：v0 阶段不做自动化；把修正内容直接写入 markdown 文件，保留文件夹副本以便回滚。

## 隐私规则

不要把 API 密钥、原始会话日志、消息数据库、`.dreams` 或 `session-corpus` 放进 persona 文件夹。
