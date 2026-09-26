#!/usr/bin/env python3
"""audit_skill_repo.py — 技能库全量审计（frontmatter 校验 / 共享脚本检测 / 镜像对检测 / 统计）。

纯标准库。扫描一个或多个技能根目录（符号链接感知，不会漏掉软链挂载的目录），
对所有 SKILL.md 做确定性检查，输出 JSON 与 Markdown 报告。

用法：
  python3 audit_skill_repo.py [--root PATH ...] [--json] [--out FILE]
  python3 audit_skill_repo.py            # 默认扫 /app/.agents/skills 与 <技能安装位>
  python3 audit_skill_repo.py --json > report.json

设计动机（人工审计实测痛点）：多轮人工读取数百个 SKILL.md 会漏统软链目录、
把"高度相似"夸大为"逐行相同"、把合法 YAML 列表误判为"语法错误"。本脚本把这些
检查全部确定性化：计数可追溯、相似度有阈值、frontmatter 错误按类型分级。
"""
import argparse, difflib, hashlib, json, os, re, sys, unicodedata

DEFAULT_ROOTS = ["/app/.agents/skills", "<技能安装位>"]
try:
    import yaml  # 环境有 PyYAML 则精确解析；没有则降级为结构嗅探
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False

EXTRA_FIELDS = ["type", "tags", "metadata", "displayName", "emoji",
                "requires", "permissions", "license", "version", "compatibility"]

def find_skill_files(roots):
    """符号链接感知地找全部 SKILL.md；按 realpath 去重。返回 [(realpath, display_path, root)]."""
    seen, out = {}, []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root, followlinks=True):
            if "SKILL.md" in files:
                p = os.path.join(dirpath, "SKILL.md")
                rp = os.path.realpath(p)
                if rp not in seen:
                    seen[rp] = (rp, p, root)
                    out.append(seen[rp])
    return out

def split_frontmatter(text):
    """返回 (frontmatter_str 或 None, body)."""
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]

def parse_frontmatter(fm):
    """返回 (data_or_None, error_or_None, error_kind)。
    error_kind: 'yaml_syntax'（真语法错）/ 'structure_list'（解析为列表）/ 'structure_other'。"""
    if not HAVE_YAML:
        # 降级嗅探：检查是否以 "- name:" 开头（列表形态）
        if re.search(r"^\s*-\s*name\s*:", fm, re.M):
            return None, "frontmatter 疑似列表形态（- name:），且环境无 PyYAML 无法精确解析", "structure_list"
        data = {}
        for line in fm.splitlines():
            m = re.match(r"^([A-Za-z_][\w.]*)\s*:\s*(.*)$", line)
            if m:
                data[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        return data, None, None
    try:
        data = yaml.safe_load(fm)
    except Exception as e:
        return None, f"YAML 语法错误: {e}", "yaml_syntax"
    if isinstance(data, list):
        return None, "frontmatter 解析为 YAML 列表而非映射（常见于误写 '- name:'）：结构不符合 skill 规范，多数加载器无法读取 name/description", "structure_list"
    if not isinstance(data, dict):
        return None, "frontmatter 解析结果非映射", "structure_other"
    return data, None, None

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def line_signature(body):
    """行集合签名（去空白/去空行），用于廉价 Jaccard 预筛。"""
    lines = set()
    for ln in body.splitlines():
        s = ln.strip()
        if s and not s.startswith("<!--"):
            lines.add(s)
    return lines

def cjk_ratio(text):
    cjk = sum(1 for ch in text if unicodedata.category(ch) == "Lo")
    return cjk / max(1, len(text))

def audit(roots):
    files = find_skill_files(roots)
    records, script_index = [], {}
    for rp, dp, root in files:
        skill_dir = os.path.dirname(dp)
        name_dir = os.path.basename(skill_dir)
        top_dir = os.path.relpath(skill_dir, root).split(os.sep)[0]
        nested = os.path.relpath(skill_dir, root).count(os.sep) > 0
        text = open(rp, encoding="utf-8", errors="replace").read()
        fm, body = split_frontmatter(text)
        rec = {"path": dp, "root": root, "dir": name_dir, "top_dir": top_dir,
               "nested": nested, "issues": [], "fm_fields": [], "fm_name": None,
               "body_lines": len(body.splitlines())}
        if fm is None:
            rec["issues"].append({"level": "P0", "kind": "no_frontmatter",
                                  "msg": "缺少 frontmatter"})
        else:
            data, err, kind = parse_frontmatter(fm)
            if err:
                rec["issues"].append({"level": "P0", "kind": kind, "msg": err})
            else:
                rec["fm_fields"] = sorted(data.keys())
                fm_name = data.get("name")
                rec["fm_name"] = fm_name
                if not fm_name:
                    rec["issues"].append({"level": "P0", "kind": "no_name", "msg": "frontmatter 缺 name"})
                else:
                    nm = str(fm_name)
                    if nm != name_dir and not nested:
                        rec["issues"].append({"level": "P1", "kind": "name_dir_mismatch",
                                              "msg": f"frontmatter name '{nm}' ≠ 目录名 '{name_dir}'"})
                    if nm != nm.lower() or " " in nm:
                        rec["issues"].append({"level": "P1", "kind": "name_case",
                                              "msg": f"name '{nm}' 非 kebab-case"})
                if not data.get("description"):
                    rec["issues"].append({"level": "P0", "kind": "no_description", "msg": "缺 description"})
                if "license" not in data:
                    rec["issues"].append({"level": "P2", "kind": "no_license", "msg": "缺 license 字段"})
        rec["_sig"] = line_signature(body)
        rec["_body"] = body
        rec["_rel"] = os.path.relpath(skill_dir, root)  # 顶层为目录名本身；嵌套含子路径
        records.append(rec)
        # 脚本索引
        sdir = os.path.join(skill_dir, "scripts")
        if os.path.isdir(sdir):
            for sp in sorted(os.listdir(sdir)):
                fp = os.path.join(sdir, sp)
                if os.path.isfile(fp):
                    h = md5_of(fp)
                    script_index.setdefault((sp, h), []).append(dp)
    # 共享脚本对
    shared_scripts = []
    for (fname, h), owners in script_index.items():
        top_dirs = sorted({r["top_dir"] for r in records if r["path"] in owners})
        if len(top_dirs) > 1:
            shared_scripts.append({"script": fname, "md5": h, "skills": top_dirs})
    # 镜像对检测：Jaccard 预筛 + difflib 精算
    # 规则：① 顶层技能之间两两可比；② 嵌套子技能仅与另一库中"相同相对子路径"的子技能可比
    #       （避免 backend-building × backend-building-swarm 21×21 交叉刷屏）；
    #       ③ 嵌套匹配按 (topA, topB) 聚合为一条，计 nested_hits。
    raw_pairs = []
    n = len(records)
    for i in range(n):
        si = records[i]["_sig"]
        if not si:
            continue
        for j in range(i + 1, n):
            a, b = records[i], records[j]
            if a["top_dir"] == b["top_dir"]:
                continue
            if a["nested"] or b["nested"]:
                if not (a["nested"] and b["nested"]):
                    continue
                sub_a = a["_rel"].split(os.sep, 1)[1]
                sub_b = b["_rel"].split(os.sep, 1)[1]
                if sub_a != sub_b:
                    continue
            sj = b["_sig"]
            if not sj:
                continue
            inter = len(si & sj)
            union = len(si | sj)
            if union and inter / union >= 0.70:
                ratio = difflib.SequenceMatcher(None, a["_body"], b["_body"]).ratio()
                if ratio >= 0.80:
                    raw_pairs.append((a, b, ratio))
    agg = {}
    for a, b, ratio in raw_pairs:
        key = tuple(sorted([a["top_dir"], b["top_dir"]]))
        lang_note = ""
        ra, rb = cjk_ratio(a["_body"]), cjk_ratio(b["_body"])
        if (ra > 0.15) != (rb > 0.15):
            lang_note = "中英文翻译镜像"
        cur = agg.get(key)
        if not cur or ratio > cur["similarity"]:
            agg[key] = {"a": key[0], "b": key[1], "similarity": round(ratio, 4),
                        "note": lang_note or "同语言",
                        "nested_hits": (cur["nested_hits"] if cur else 0)}
        agg[key]["nested_hits"] = agg[key].get("nested_hits", 0) + (1 if a["nested"] else 0)
    pairs = []
    for p in agg.values():
        r = p["similarity"]
        p["grade"] = ("逐行相同级" if r >= 0.98 else
                      "高度相似" if r >= 0.90 else "镜像/近似")
        if p["nested_hits"] > 1:
            p["note"] += f"，嵌套 {p['nested_hits']} 处"
        pairs.append(p)
    pairs.sort(key=lambda p: -p["similarity"])
    stats = {
        "skill_md_total": len(records),
        "top_level_dirs": len({r["top_dir"] for r in records}),
        "nested_skills": sum(1 for r in records if r["nested"]),
        "roots_scanned": [r for r in roots if os.path.isdir(r)],
        "roots_missing": [r for r in roots if not os.path.isdir(r)],
        "shared_script_groups": len(shared_scripts),
        "mirror_pairs_detected": len(pairs),
        "p0_issues": sum(1 for r in records for i in r["issues"] if i["level"] == "P0"),
        "p1_issues": sum(1 for r in records for i in r["issues"] if i["level"] == "P1"),
        "p2_issues": sum(1 for r in records for i in r["issues"] if i["level"] == "P2"),
    }
    for r in records:
        r.pop("_sig", None); r.pop("_body", None); r.pop("_rel", None)
    return {"stats": stats, "shared_scripts": shared_scripts,
            "mirror_pairs": pairs, "records": records}

def to_markdown(rep):
    s = rep["stats"]
    out = ["# 技能库审计报告", "", "## 统计", "",
           f"- SKILL.md 总数：**{s['skill_md_total']}**（顶层目录 {s['top_level_dirs']}，嵌套子技能 {s['nested_skills']}）",
           f"- 扫描根：{', '.join(s['roots_scanned']) or '无'}" + (f"；⚠️ 缺失根：{', '.join(s['roots_missing'])}" if s["roots_missing"] else ""),
           f"- 共享脚本组：{s['shared_script_groups']}；镜像对候选：{s['mirror_pairs_detected']}",
           f"- 问题计数：P0={s['p0_issues']} P1={s['p1_issues']} P2={s['p2_issues']}", ""]
    if rep["shared_scripts"]:
        out += ["## 共享脚本（同一脚本被多个技能引用，md5 逐字节相同）", "",
                "| 脚本 | md5(短) | 引用技能 |", "|---|---|---|"]
        for g in rep["shared_scripts"]:
            out.append(f"| {g['script']} | {g['md5'][:8]} | {', '.join(g['skills'])} |")
        out.append("")
    if rep["mirror_pairs"]:
        out += ["## 镜像对候选（相似度 ≥0.80）", "",
                "| Skill A | Skill B | 相似度 | 分级 | 备注 |", "|---|---|---|---|---|"]
        for p in rep["mirror_pairs"]:
            out.append(f"| {p['a']} | {p['b']} | {p['similarity']:.3f} | {p['grade']} | {p['note']} |")
        out.append("")
    p0 = [(r, i) for r in rep["records"] for i in r["issues"] if i["level"] == "P0"]
    if p0:
        out += ["## P0 问题", "", "| 技能 | 类型 | 说明 |", "|---|---|---|"]
        for r, i in p0:
            out.append(f"| {r['top_dir']} | {i['kind']} | {i['msg']} |")
        out.append("")
    p1 = [(r, i) for r in rep["records"] for i in r["issues"] if i["level"] == "P1"]
    if p1:
        out += ["## P1 问题", "", "| 技能 | 类型 | 说明 |", "|---|---|---|"]
        for r, i in p1:
            out.append(f"| {r['top_dir']} | {i['kind']} | {i['msg']} |")
        out.append("")
    out += ["---", "*术语纪律：'逐行相同级' = difflib 相似度 ≥0.98；'高度相似' ≥0.90；'镜像/近似' ≥0.80。",
            "禁止把 '高度相似' 表述为 '逐行相同'。frontmatter 'structure_list' 是结构不合规，不是 YAML 语法错误。*"]
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser(description="技能库全量审计：frontmatter 校验 / 共享脚本 / 镜像对 / 统计（符号链接感知）")
    ap.add_argument("--root", action="append", default=None, help="技能根目录，可重复；默认扫内置+用户技能库")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    ap.add_argument("--out", help="把 Markdown 报告写入文件")
    args = ap.parse_args()
    roots = args.root or DEFAULT_ROOTS
    rep = audit(roots)
    if not HAVE_YAML:
        print("WARNING: 无 PyYAML，frontmatter 解析为降级嗅探模式", file=sys.stderr)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        md = to_markdown(rep)
        print(md)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
