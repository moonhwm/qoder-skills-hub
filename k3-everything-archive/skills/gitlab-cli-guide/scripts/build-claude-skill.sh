#!/usr/bin/env bash
# build-claude-skill.sh
#
# 生成 claude-skill.zip — 一个仅包含单个 SKILL.md 的 zip 压缩包，适用于上传至
# Claude.ai 组织设置（该设置要求必须且只能包含一个 SKILL.md）。
#
# 用法：
#   bash scripts/build-claude-skill.sh [--output <path>] [--root <repo-root>]
#
# 选项：
#   --output  输出 zip 文件的路径（默认值：./claude-skill.zip）
#   --root    仓库根目录（默认值：此脚本的父目录）
#
# 输出：
#   claude-skill.zip 包含一个合并后的 SKILL.md
#
# 合并后的文件包含：
#   1. 顶层 SKILL.md（已移除 OpenClaw 的 frontmatter）
#   2. 按字母顺序排列的每个子技能 SKILL.md（已移除 frontmatter）

set -euo pipefail

# ── 解析路径 ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_ZIP="$REPO_ROOT/claude-skill.zip"

# ── 解析参数 ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT_ZIP="$2"; shift 2 ;;
    --root)   REPO_ROOT="$2";  shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── 临时工作区 ────────────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

MERGED="$WORK_DIR/SKILL.md"

# ── 辅助函数：移除 YAML frontmatter 并输出内容 ───────────────────────────
# Frontmatter 是第一对 `---` 行之间的内容块。
strip_frontmatter() {
  local file="$1"
  awk '
    BEGIN { in_front=0; done=0 }
    /^---$/ && !done {
      if (!in_front) { in_front=1; next }
      else           { in_front=0; done=1; next }
    }
    !in_front { print }
  ' "$file"
}

# ── 构建合并后的 SKILL.md ─────────────────────────────────────────────────────
echo "Building merged SKILL.md from $REPO_ROOT..."

# 必需的 YAML frontmatter (Claude.ai 需要 name + description)
cat >> "$MERGED" <<'FRONTMATTER'
---
name: gitlab-cli-skills
description: Comprehensive GitLab CLI (glab) command reference and workflows for all GitLab operations. Use when working with merge requests, CI/CD pipelines, issues, releases, repositories, authentication, variables, labels, milestones, snippets, or any glab command. Covers 37+ sub-commands including glab mr, glab ci, glab issue, glab repo, glab release, glab variable, and more.
dependencies:
  - glab
---

FRONTMATTER

# 简介正文
cat >> "$MERGED" <<'INTRO'
# GitLab CLI 技巧 —— glab 全面参考

This skill provides complete reference and workflows for the GitLab CLI (`glab`).
It covers authentication, merge requests, CI/CD pipelines, issues, releases,
repositories, and 30+ other glab commands.

---

INTRO

# 1. 顶层技能（概述 + 路由）—— 移除其 frontmatter，因为我们已自行编写
TOP_LEVEL="$REPO_ROOT/SKILL.md"
if [[ -f "$TOP_LEVEL" ]]; then
  echo "## Overview" >> "$MERGED"
  echo "" >> "$MERGED"
  strip_frontmatter "$TOP_LEVEL" >> "$MERGED"
  echo "" >> "$MERGED"
  echo "---" >> "$MERGED"
  echo "" >> "$MERGED"
fi

# 2. 按字母顺序排列的子技能（包含 SKILL.md 文件的任意目录，
#    排除根目录本身及 scripts/ 目录）
mapfile -t SUB_SKILLS < <(
  find "$REPO_ROOT" -mindepth 2 -maxdepth 2 -name "SKILL.md" \
    ! -path "$REPO_ROOT/scripts/*" \
    | sort
)

TOTAL=${#SUB_SKILLS[@]}
COUNT=0

for skill_file in "${SUB_SKILLS[@]}"; do
  sub_dir="$(basename "$(dirname "$skill_file")")"
  COUNT=$((COUNT + 1))
  echo "  [$COUNT/$TOTAL] $sub_dir"

  # 源自目录名的章节标题（例如：glab-mr → glab mr）
  heading="${sub_dir//-/ }"

  {
    echo "## $heading"
    echo ""
    strip_frontmatter "$skill_file"
    echo ""
    echo "---"
    echo ""
  } >> "$MERGED"
done

# ── 打包为 zip ──────────────────────────────────────────────────────────
# Claude.ai 要求文件位于子目录内，而非 zip 包的根目录：
#   claude-skill.zip
#    └── gitlab-cli-skills/
#        └── SKILL.md
rm -f "$OUTPUT_ZIP"

# 如果可用则使用 zip，否则回退到 python3（始终存在）
if command -v zip &>/dev/null; then
  mkdir -p "$WORK_DIR/gitlab-cli-skills"
  cp "$MERGED" "$WORK_DIR/gitlab-cli-skills/SKILL.md"
  (cd "$WORK_DIR" && zip -qr "$OUTPUT_ZIP" gitlab-cli-skills/)
else
  python3 -c "
import zipfile, sys
output, source = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(source, 'gitlab-cli-skills/SKILL.md')
" "$OUTPUT_ZIP" "$MERGED"
fi

LINES=$(wc -l < "$MERGED")
SIZE=$(wc -c < "$MERGED")
echo ""
echo "✅ Done."
echo "   Merged:  $TOTAL sub-skills + top-level"
echo "   Lines:   $LINES"
echo "   Size:    $SIZE bytes"
echo "   Output:  $OUTPUT_ZIP"
