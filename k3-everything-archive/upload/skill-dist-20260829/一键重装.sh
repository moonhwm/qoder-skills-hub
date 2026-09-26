#!/bin/bash
# 一键重装四包（2026-08-29）——在您的 Kimi Work 终端整段粘贴执行
set -e
D=<上传区>/skill-dist-20260829
S=<技能安装位>
for pkg in autonomous-advance-ops skill-dispatch-hq plugin-datasource-ops rumor-chain-verifier; do
  rm -rf "$S/$pkg".new && mkdir -p "$S/$pkg".new
  unzip -oq "$D/$pkg.skill" -d "$S/$pkg".new
  rm -rf "$S/$pkg".bak && [ -d "$S/$pkg" ] && mv "$S/$pkg" "$S/$pkg".bak || true
  mv "$S/$pkg".new "$S/$pkg"
  echo "[OK] $pkg 重装完成（旧版备份于 $pkg.bak）"
done
echo "全部完成。验证口令：确认 autonomous-advance-ops 版本 → 应应答 v1.0.5"
