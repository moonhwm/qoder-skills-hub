#!/usr/bin/env python3
"""build_skill_index.py - 生成 MASTER_SKILL_INDEX.md（技能全量索引）

扫描 <技能安装位>/（用户技能，跨会话持久）与 /app/.agents/skills/（内置库）
下所有 SKILL.md 的 frontmatter，提取 技能名 / 触发词摘要 / 一句话用途，
写入 <上传区>/MASTER_SKILL_INDEX.md；upload 不可写时退写
<输出区>/MASTER_SKILL_INDEX.md 并提示用户手动转移。

用法：
    python3 build_skill_index.py              # 扫描两个技能目录
    python3 build_skill_index.py --user-only  # 只扫用户技能目录
    python3 build_skill_index.py --out PATH   # 自定义输出路径

纯标准库实现，无第三方依赖。
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

USER_SKILLS_DIR = Path("<技能安装位>")
BUILTIN_SKILLS_DIR = Path("/app/.agents/skills")
UPLOAD_DIR = Path("<上传区>")
OUTPUT_DIR = Path("<输出区>")
INDEX_NAME = "MASTER_SKILL_INDEX.md"
# 中文名称兜底注册表：当 description 中缺失「中文名：XX」时，按技术名称查表；若文件不存在则跳过且不报错
ALIASES_PATH = UPLOAD_DIR / "skill-iteration-registry" / "skill_aliases.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELD_RE = re.compile(r"^(name|description)\s*:\s*(.*)$")
CN_NAME_RE = re.compile(r"中文名[：:]\s*([^，。,\"']+)")


def load_aliases() -> dict:
    """读取 skill_aliases.json 的 aliases 表作为中文名兜底；文件缺失/损坏时返回空表。"""
    try:
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        aliases = data.get("aliases", {})
        return aliases if isinstance(aliases, dict) else {}
    except (OSError, ValueError):
        return {}


def extract_cn_name(name: str, description: str, aliases: dict) -> str:
    """中文名优先级：description 尾部「中文名：XX」 > aliases 注册表 > —。"""
    m = CN_NAME_RE.search(description)
    if m:
        return m.group(1).strip()
    return aliases.get(name, "—")


def parse_frontmatter(skill_md: Path) -> dict:
    """从 SKILL.md 提取 name/description（容忍带引号的多行写法，够用即可）。"""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    fields = {}
    current_key = None
    for line in body.splitlines():
        fm = FIELD_RE.match(line)
        if fm:
            current_key = fm.group(1)
            fields[current_key] = fm.group(2).strip().strip('"').strip("'")
        elif not line.startswith((" ", "\t")):
            # 遇到其他顶层键（license/metadata/...）即结束 description 续行
            current_key = None
        elif current_key == "description":
            # YAML 折叠续行：仅拼接纯文本行；带 key: 形态的缩进行是
            # metadata 等嵌套子键（如 version: "1.0.0"），拼入会污染触发词
            if not re.match(r"^\s*[\w.-]+\s*:", line):
                fields[current_key] += " " + line.strip()
    return fields


# 仅匹配成对引号内的词：「」、“”、"…"；不再混配直引号，避免英文 frontmatter
# 产出 "1.0.0"、"tags: [" 这类垃圾词。
PAIRED_QUOTES_RE = re.compile(
    r"「([^「」\n]{2,20})」|“([^“”\n]{2,20})”|\"([^\"\n]{2,20})\""
)
CJK_RE = re.compile(r"[一-鿿]")


def summarize_trigger_words(description: str, max_words: int = 8) -> str:
    """从 description 摘出成对引号（「」、“”、"…"）内的词作为触发词摘要。"""
    triggers = []
    for m in PAIRED_QUOTES_RE.finditer(description):
        triggers.append(next(g for g in m.groups() if g is not None))
    seen, out = set(), []
    for t in triggers:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    if out:
        return "、".join(out[:max_words])
    # 无引号词：纯英文 description 显示占位，避免噪音
    if not CJK_RE.search(description):
        return "(en) see description"
    return "（description 未列显式触发词）"


def one_line_purpose(description: str, max_len: int = 80) -> str:
    """取 description 第一句（冒号/句号前）作为一句话用途。"""
    head = re.split(r"[：:。]", description, maxsplit=1)[0].strip()
    head = re.sub(r"\s+", " ", head)
    return head[:max_len] + ("…" if len(head) > max_len else "")


def scan_dir(root: Path, is_user_skill: bool, aliases: dict) -> list:
    rows = []
    if not root.is_dir():
        return rows
    for skill_md in sorted(root.glob("*/SKILL.md")):
        fm = parse_frontmatter(skill_md)
        name = fm.get("name") or skill_md.parent.name
        desc = fm.get("description", "")
        rows.append({
            "name": name,
            "cn_name": extract_cn_name(name, desc, aliases),
            "path": str(skill_md.parent),
            "triggers": summarize_trigger_words(desc),
            "purpose": one_line_purpose(desc) if desc else "（无 description）",
            "is_user": is_user_skill,
        })
    return rows


def render_index(user_rows: list, builtin_rows: list, scanned_dirs: list) -> str:
    lines = [
        "# MASTER_SKILL_INDEX - 技能全量索引",
        "",
        f"> 由 `cross-session-workflow-bridge/scripts/build_skill_index.py` 于 {date.today().isoformat()} 生成。",
        "> 用法：新会话开场读本索引 → 对照任务列出相关技能 → 请用户一次确认勾选。",
        "> 刷新：`python3 build_skill_index.py [--user-only]`（技能增删改后必跑）。",
        "",
        f"扫描目录：{'; '.join(scanned_dirs)}",
        "",
        f"## 用户技能（<技能安装位>/，跨会话持久，共 {len(user_rows)} 个）",
        "",
        "| 技能名 | 中文名 | 一句话用途 | 触发词摘要 | 路径 | 用户技能 |",
        "|---|---|---|---|---|---|",
    ]
    for r in user_rows:
        lines.append(f"| {r['name']} | {r['cn_name']} | {r['purpose']} | {r['triggers']} | {r['path']} | 是 |")
    lines += [
        "",
        f"## 内置技能（/app/.agents/skills/，平台库，共 {len(builtin_rows)} 个）",
        "",
        "| 技能名 | 中文名 | 一句话用途 | 触发词摘要 | 路径 | 用户技能 |",
        "|---|---|---|---|---|---|",
    ]
    for r in builtin_rows:
        lines.append(f"| {r['name']} | {r['cn_name']} | {r['purpose']} | {r['triggers']} | {r['path']} | 否 |")
    lines += [
        "",
        "## 备注",
        "",
        "- 用户新建技能务必写入 <技能安装位>/；写入 /app/.agents/skills/ 不持久（真实事故：amap-travel-skill 两次丢失）。",
        "- 本索引应存放于 <上传区>/ 以跨会话可见；若本文件出现在 <输出区>/，请手动转移到 upload。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 MASTER_SKILL_INDEX.md 技能全量索引")
    ap.add_argument("--user-only", action="store_true", help="只扫描 <技能安装位>/")
    ap.add_argument("--out", default=None, help="自定义输出路径（默认自动选 upload，不可写时退 output）")
    args = ap.parse_args()

    aliases = load_aliases()
    user_rows = scan_dir(USER_SKILLS_DIR, is_user_skill=True, aliases=aliases)
    builtin_rows = [] if args.user_only else scan_dir(BUILTIN_SKILLS_DIR, is_user_skill=False, aliases=aliases)
    scanned = [str(USER_SKILLS_DIR)] + ([] if args.user_only else [str(BUILTIN_SKILLS_DIR)])

    if not user_rows and not builtin_rows:
        print("⚠️ 未扫描到任何 SKILL.md，检查技能目录是否存在。", file=sys.stderr)
        return 1

    content = render_index(user_rows, builtin_rows, scanned)

    if args.out:
        out_path = Path(args.out)
    elif _writable(UPLOAD_DIR):
        out_path = UPLOAD_DIR / INDEX_NAME
    else:
        out_path = OUTPUT_DIR / INDEX_NAME
        print(f"⚠️ {UPLOAD_DIR} 不可写，索引已退写到 {out_path}；"
              f"请手动转移到 {UPLOAD_DIR}/ 以便跨会话可见。", file=sys.stderr)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
    except OSError as e:
        print(f"❌ 写入失败 {out_path}: {e}", file=sys.stderr)
        return 1

    print(f"✅ 索引已生成：{out_path}")
    print(f"   用户技能 {len(user_rows)} 个，内置技能 {len(builtin_rows)} 个。")
    return 0


def _writable(d: Path) -> bool:
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(main())
