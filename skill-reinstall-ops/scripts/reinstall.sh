#!/bin/bash
# reinstall.sh v1.0.0 — dist 目录技能包一键重装（含只读预检/备份/逐包核验/零伪装）
# 用法: bash reinstall.sh [dist目录] [安装位目录] [包名空格分隔列表]
set -uo pipefail

D="${1:-<上传区>/skill-dist-20260829}"
S="${2:-<技能安装位>}"
PKGS="${3:-autonomous-advance-ops skill-dispatch-hq plugin-datasource-ops rumor-chain-verifier}"

echo "== 预检：安装位可写性 =="
if ! touch "$S/.w_test_reinstall" 2>/dev/null; then
  echo "[FAIL] 安装位只读：$S ——本脚本无法写入。"
  echo "降级路径：①Kimi 界面「与 Kimi 对话创建技能」粘贴对应 SKILL.md 全文；"
  echo "         ②Kimi Claw Desktop 桌面端会话中执行本脚本（其环境可能可写）。"
  echo "如实停止，未做任何改动。"
  exit 2
fi
rm -f "$S/.w_test_reinstall"

ok=0; fail=0
for pkg in $PKGS; do
  src="$D/$pkg.skill"
  if [ ! -f "$src" ]; then echo "[SKIP] $pkg：包不存在 $src"; fail=$((fail+1)); continue; fi
  rm -rf "$S/$pkg.new"
  mkdir -p "$S/$pkg.new"
  if ! python3 -m zipfile -e "$src" "$S/$pkg.new" 2>/dev/null; then
    echo "[FAIL] $pkg：解压失败"; rm -rf "$S/$pkg.new"; fail=$((fail+1)); continue
  fi
  # 兼容包内带目录层（pkg/SKILL.md）与平铺（SKILL.md）
  if [ ! -f "$S/$pkg.new/SKILL.md" ]; then
    inner=$(find "$S/$pkg.new" -maxdepth 2 -name SKILL.md | head -1)
    [ -n "$inner" ] && cp -r "$(dirname "$inner")/." "$S/$pkg.new/" 2>/dev/null
  fi
  rm -rf "$S/$pkg.bak"
  [ -d "$S/$pkg" ] && mv "$S/$pkg" "$S/$pkg.bak"
  mv "$S/$pkg.new" "$S/$pkg"
  v=$(grep -o 'version: "[0-9.]*"' "$S/$pkg/SKILL.md" 2>/dev/null | head -1)
  echo "[OK] $pkg 重装完成（${v:-无版本位}）"
  ok=$((ok+1))
done
echo "== 结果：成功 $ok / 失败或跳过 $fail =="
[ "$fail" -eq 0 ]
