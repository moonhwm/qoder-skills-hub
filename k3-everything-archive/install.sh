#!/bin/sh
# K3 技能库安装器（HarmonyOS/Linux/macOS 形态，POSIX sh）
# 用法： sh install.sh [目标技能位路径]
set -e
TARGET="${1:-$HOME/.k3-skills}"
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
echo "== K3 Skill Library Installer (HarmonyOS/Linux) =="
mkdir -p "$TARGET"
cp -r "$HERE/skills/." "$TARGET/"
echo "已复制技能至 $TARGET"
python3 "$HERE/verify_install.py" --target "$TARGET" --manifest "$HERE/MANIFEST.json" && echo "INSTALL PASS"
