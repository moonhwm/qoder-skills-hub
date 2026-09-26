#!/bin/sh
# skill-refresh-ops 步骤①②⑤确定性执行：预检写入权限 + 全库版本漂移盘点 + dist 包源搜索
# 用法: sh refresh_check.sh [upload_dir]   默认 upload_dir=<上传区>
# 输出: 报告写入 <输出区>/skill_refresh_report_<日期>.txt 并打印关键结论
set -u
UPLOAD="${1:-<上传区>}"
OUT="<输出区>/skill_refresh_report_$(date +%Y%m%d_%H%M%S).txt"

{
echo "===== skill-refresh-ops 刷新报告 $(date '+%F %T') ====="
echo
echo "[① 安装位可写性预检]"
if touch <技能安装位>/.writetest 2>/dev/null; then
  rm -f <技能安装位>/.writetest
  echo "USER_SKILLS=WRITABLE（可移交 skill-reinstall-ops）"
else
  echo "USER_SKILLS=READ-ONLY（重装如实停止，禁止假装成功）"
fi
echo
echo "[② 库盘点与版本漂移]"
U=$(ls <技能安装位> 2>/dev/null | wc -l)
A=$(ls /app/.agents/skills 2>/dev/null | wc -l)
echo "user_skills=$U  builtin_skills=$A"
echo "-- 含 version 字段的用户技能 --"
for s in <技能安装位>/*/SKILL.md; do
  v=$(grep -m1 '^  version:' "$s" 2>/dev/null | tr -d '"' | awk '{print $2}')
  [ -n "$v" ] && echo "$(basename "$(dirname "$s")")|$v"
done | sort
echo
echo "[⑤ dist 包源搜索（$UPLOAD）]"
FOUND=$(find "$UPLOAD" -maxdepth 3 \( -iname '*.skill' -o -iname 'skill-dist*' \) 2>/dev/null)
if [ -n "$FOUND" ]; then echo "PACKAGES_FOUND:"; echo "$FOUND"; else echo "PACKAGES_FOUND=NONE"; fi
echo
echo "[结论] 移交重装条件=可写∧有包；缺一即如实停止并给降级路径。"
} | tee "$OUT"
