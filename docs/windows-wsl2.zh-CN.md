# Windows WSL2 指南

v0 版本不提供原生 Windows 服务支持。请使用 WSL2。

## 支持的路径

1. 安装 WSL2，选择 Ubuntu 发行版。
2. 在 Linux 文件系统中工作，不要使用 Windows 挂载路径。
3. 在 WSL2 内安装 Python 3、Node.js 18+、npm 和 OpenClaw。
4. 运行 `python3 scripts/clawbot_doctor.py`。

## 限制

- 不支持原生 Windows 服务。
- 本项目未验证原生 Windows 环境下的微信登录行为。
- `/mnt/c` 下的文件权限行为可能不一致；请把项目放在 WSL home 目录下。

## 建议的下一步

本地验证通过后，如果需要稳定的长时在线，使用云端迁移方案。
