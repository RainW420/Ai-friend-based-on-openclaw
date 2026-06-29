# Clawbot 云端迁移指南

## 目的

这份指南说明将来如何把 Clawbot 运行时迁移到云服务器。当前版本完成了工具链开发和本地验证，实际的云端迁移尚未执行。

## 目标架构

云服务器运行以下服务：

- OpenClaw Gateway，绑定 loopback 端口 `18789`
- 微信 channel，手动登录后启用
- `clawbot-readonly` 插件
- 外部心跳执行器
- 若服务器内存充足，运行 `ollama` + `bge-m3` 做记忆搜索

本地机器保留：

- 开发和审查工作区
- 紧急回滚目标

## 最低服务器建议

- 最低试运行：2 vCPU，2 GiB 内存，40 GiB 磁盘，3 Mbps 带宽
- 推荐配置：2 vCPU，4-8 GiB 内存，40-80 GiB 磁盘，3-5 Mbps 带宽

2 GiB 内存足以支撑基础的 Gateway 和微信对接（通过 DeepSeek API），但跑 Ollama 和记忆索引会偏紧。

## 本地导出

```bash
python3 scripts/cloud_runtime_inventory.py --json
python3 scripts/export_runtime_bundle.py --output /tmp/clawbot-cloud-runtime.tar.gz
python3 scripts/restore_runtime_bundle.py --bundle /tmp/clawbot-cloud-runtime.tar.gz --target /tmp/clawbot-cloud-restore
```

## 云端初始化流程

在云服务器就绪后，手动执行以下步骤：

```bash
sudo useradd -m -s /bin/bash clawbot
sudo mkdir -p /opt/clawbot
sudo chown -R clawbot:clawbot /opt/clawbot
```

把 bundle 拷贝到服务器上，然后以 `clawbot` 用户身份操作：

```bash
mkdir -p /opt/clawbot
tar -xzf clawbot-cloud-runtime.tar.gz -C /opt/clawbot
cd /opt/clawbot/clawbot-runtime
```

安装与本地相同大版本的 Node 和 OpenClaw。手动重建 OpenClaw secrets，**不要**复制 `~/.openclaw/secrets.json`。

## 切换步骤

1. 云端准备好之前，保持本地 OpenClaw Gateway 正常运行，暂不登录微信。
2. 云端验证配置和 Gateway loopback 绑定。
3. 云端登录微信之前，先停止本地 Gateway。
4. 在云端登录微信。
5. 验证一次手动私信收发。
6. 不带 `--send` 运行心跳执行器。
7. 只在 dry-run 日志确认无误后，才启用心跳 timer。

## 回滚

如果云端微信或 Gateway 出现故障：

1. 停止云端 Gateway 和心跳 timer。
2. 启动本地 OpenClaw Gateway。
3. 如有必要，在本地重新登录微信。
4. 执行 `openclaw channels status` 确认状态。

## 烟雾测试

```bash
openclaw config validate
openclaw secrets audit
openclaw gateway status
openclaw channels status
openclaw memory status --agent clawbot --deep
python3 scripts/clawbot_runtime_status.py --json
python3 scripts/clawbot_heartbeat_runner.py --now 2026-06-28T21:00:00+08:00
```

烟雾测试期间**不要**给心跳命令加 `--send`。

## 安全规则

- Gateway 仅绑定 loopback。
- 仅允许 SSH 密钥登录。
- 云防火墙仅开放 SSH 端口。
- `tools.exec.mode` 保持 `deny`。
- `affectiveState.injectToMainModel` 保持 `false`。
- 导出包中不包含任何密钥值。
