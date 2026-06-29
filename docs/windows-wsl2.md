# Windows WSL2 Guide

Native Windows service support is not part of v0. Use WSL2.

## Supported Path

1. Install WSL2 with Ubuntu.
2. Work inside the Linux filesystem, not a mounted Windows path.
3. Install Python 3, Node.js 18+, npm, and OpenClaw inside WSL2.
4. Run `python3 scripts/clawbot_doctor.py`.

## Limitations

- Native Windows services are not supported.
- Native Windows Weixin login behavior is not validated by this project.
- File permission behavior may differ on `/mnt/c`; keep the project under the WSL home directory.

## Recommended Next Step

After local validation, use cloud migration if you need stable long-running availability.
