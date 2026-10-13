#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""govdoc_precheck.py — 公文合规预检门·术语闸机检 + 最小骨架检查 + 编码闸（--doccode）。

用法:
  python3 govdoc_precheck.py <file.md>            # 术语闸全检 + 骨架恒检
  python3 govdoc_precheck.py <file.md> --skeleton-only
  python3 govdoc_precheck.py <file.md> --doccode  # 追加编码闸（件号语法/撞号/断档/无号）
  python3 govdoc_precheck.py <file.md> --json
  python3 govdoc_precheck.py --self-test

裁定依据: references/terminology.md（双框架词表/禁用清单/模糊术语裁定）；
          references/doccode-spec.md（编码闸：L1 公文形制要素单/L2 件号谱系语法）。
台账: references/doccode_registry.jsonl（哈希链 append-only；撞号以提交序先到先得）。
纪律: 检出问题改文档不改闸；闸的误判修订走技能版本流。
"""
import json, re, sys
from pathlib import Path

# ── 编码闸：L2 谱系正则（与 doccode-spec.md §3.2 同步，改谱系先改规格书） ──
SERIES = {
    "CL": r"^CL-[A-Z]+-\d{8}-[A-Z0-9]+-\d{2}$",
    "DF": r"^DF-(NOTICE|ORD|MIN)-\d{4}-\d{4}-[A-Z0-9]+-\d{2,}$",
    "TREE": r"^TREE-[A-Z0-9]+-\d{4}-\d{4}-\d{2}$",
    "EVT": r"^EVT-\d{8}-[A-Z]+-\d{3}$",
    "WK": r"^WK-\d{4}-\d{4}-\d{2}$",
    "OTL": r"^OTL-[A-Z]+-\d{3}$",
    "GW": r"^GW-[A-Z]+-\d{4}-\d{4}-\d{2}$",
    "BC": r"^BC-\d{3}$",
}
# 件号候选抽取：大写字母/数字与连字符构成、至少含一个连字符、含日期或序号段
CODE_LIKE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){2,}\b")
REGISTRY = Path(__file__).resolve().parent.parent / "references" / "doccode_registry.jsonl"

BANNED = {  # 词形: (类别, 裁定)
    "我觉得": ("个人视角口语", "error"), "我认为": ("个人视角口语", "error"),
    "可能吧": ("个人视角口语", "error"), "大概": ("个人视角口语", "warning"),
    "也许": ("个人视角口语", "warning"), "差不多": ("个人视角口语", "warning"),
    "变现": ("商业视角", "error"), "卖点": ("商业视角", "error"),
    "打法": ("商业视角", "error"), "闭环营销": ("商业视角", "error"), "私域": ("商业视角", "error"),
    "搞定": ("外来混杂", "error"), "搞得定": ("外来混杂", "error"),
    "彻底解决": ("夸张无据", "error"), "绝对安全": ("夸张无据", "error"),
}
# 「赋能」仅商业语境禁用：命中但同句含「使能/能力接口」豁免——从简：命中即 warning 交人工
BANNED_WARN = {"赋能": ("商业语境待裁", "warning")}
VAGUE = ["相关", "等等", "之类", "若干", "一定程度上"]
DEFINING = ["是指", "定义为", "包括", "分为", "指标为", "阈值为"]
SELF_OK = ["本席", "筹备组", "筹备处", "主权人", "机主"]
SELF_BAD = ["笔者", "我司", "我们团队", "小弟"]

# v0.3.0 增量：自更新链接检测（金山云存储等逐次重签的签名直链）。
# 命中即 warning：链接字面随时间漂移，破坏字节级比对与哈希留痕；归档文书应改用入口页链接。
SELF_REFRESHING_URL = [
    (re.compile(r"kss\.ksyun\.com|ks3-cn|ksyun.*X-Kss-Signature", re.I), "金山云存储签名直链"),
    (re.compile(r"[?&]X-Kss-Signature=", re.I), "金山云存储签名直链"),
    (re.compile(r"[?&]X-Amz-Signature=", re.I), "AWS 签名直链"),
    (re.compile(r"[?&]Expires=\d{6,}"), "带时效参数的签名链接"),
]

def scan(path):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    issues, urls = [], []
    in_code = False
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("```") or ln.strip().startswith("~~~"):
            in_code = not in_code
        # v0.2.1：URL 字符集截断（仅 ASCII URL 字符，全角标点/汉字天然止配）+ 句尾 ASCII 标点剥离
        for u in re.findall(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'*+,;=%\\]+", ln):
            u = u.rstrip(".,;:!?'\"\\]")  # 句尾标点与 markdown 链接方括号残尾剥离
            if u:
                urls.append({"line": i, "url": u})
                for pat, cat in SELF_REFRESHING_URL:
                    if pat.search(u):
                        issues.append({"line": i, "kind": "self_refreshing_url", "word": u[:50],
                                       "category": f"自更新链接（{cat}）：字面随时间漂移，归档文书宜改用入口页链接",
                                       "severity": "warning", "excerpt": ln.strip()[:60]})
                        break
        if in_code:
            continue  # 代码块内不查术语（引文/日志豁免），链接仍登记
        for w, (cat, sev) in list(BANNED.items()) + list(BANNED_WARN.items()):
            if w in ln:
                if w == "闭环营销":
                    pass
                issues.append({"line": i, "kind": "banned", "word": w, "category": cat, "severity": sev,
                               "excerpt": ln.strip()[:60]})
        for w in SELF_BAD:
            if w in ln:
                issues.append({"line": i, "kind": "self_reference", "word": w,
                               "category": "自称失范（规范：本席/筹备组/主权人/机主）", "severity": "error",
                               "excerpt": ln.strip()[:60]})
        if any(d in ln for d in DEFINING):
            for v in VAGUE:
                if v in ln:
                    issues.append({"line": i, "kind": "vague_in_definition", "word": v,
                                   "category": "模糊术语在关键定义位", "severity": "error",
                                   "excerpt": ln.strip()[:60]})
        elif any(v in ln for v in VAGUE):
            hit = [v for v in VAGUE if v in ln][0]
            issues.append({"line": i, "kind": "vague_narrative", "word": hit,
                           "category": "叙述位模糊术语（建议枚举）", "severity": "warning",
                           "excerpt": ln.strip()[:60]})
    return {"file": path, "issues": issues, "urls": urls,
            "url_count": len(urls), "self_reference_ok": any(s in text for s in SELF_OK)}

def _load_registry():
    """读台账并复算哈希链；链断即报（改史侦测）。返回 (rows, chain_ok)。"""
    import hashlib
    if not REGISTRY.exists():
        return [], None
    rows, prev, ok = [], "GENESIS", True
    for ln in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        core = {k: r[k] for k in ("seq", "code", "series", "doc", "seat", "date", "status")}
        h = hashlib.sha256((json.dumps(core, ensure_ascii=False, separators=(",", ":")) + prev).encode("utf-8")).hexdigest()
        if r.get("prev_hash") != prev or r.get("sha256") != h:
            ok = False
        prev = r.get("sha256", prev)
        rows.append(r)
    return rows, ok

def doccode(path, doc_id=None):
    """编码闸：抽号→语法校验→声明撞号/未入册→断档→无号提示。
    doc_id=本件声明件号（「件号：」行提取）；引用他件已入册件号放行。"""
    import os as _os
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    issues, codes = [], []
    in_code = False
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("```") or ln.strip().startswith("~~~"):
            in_code = not in_code
        if in_code:
            continue
        ln = re.sub(r"`[^`]*`", "", ln)  # 行内代码段豁免（防正则源码误判为件号）
        for m in CODE_LIKE.findall(ln):
            codes.append((i, m))
    rows, chain_ok = _load_registry()
    if chain_ok is False:
        issues.append({"line": 0, "kind": "registry_chain", "word": "doccode_registry.jsonl",
                       "category": "台账哈希链断链（疑似改史）", "severity": "error", "excerpt": ""})
    elif chain_ok is None:
        issues.append({"line": 0, "kind": "registry_missing", "word": "doccode_registry.jsonl",
                       "category": "台账缺失（撞号/断档判定降级为提示）", "severity": "warning", "excerpt": ""})
    reg = {r["code"]: r for r in rows}
    seen_here = set()
    for i, c in codes:
        if c in seen_here:
            continue
        seen_here.add(c)
        prefix = c.split("-")[0]
        if prefix not in SERIES:
            issues.append({"line": i, "kind": "doccode_unregistered", "word": c,
                           "category": "谱系未注册（须先入 doccode-spec §3.2）", "severity": "warning",
                           "excerpt": ""})
            continue
        if not re.match(SERIES[prefix], c):
            issues.append({"line": i, "kind": "doccode_syntax", "word": c,
                           "category": f"件号不合 {prefix} 谱系制式", "severity": "error",
                           "excerpt": ""})
            continue
        hit = reg.get(c)
        if doc_id and c == doc_id:
            if not hit:
                issues.append({"line": i, "kind": "doccode_not_registered", "word": c,
                               "category": "本件件号未入册（先登记后使用）", "severity": "error",
                               "excerpt": ""})
            elif hit.get("doc") and _os.path.basename(hit["doc"]) != _os.path.basename(path):
                issues.append({"line": i, "kind": "doccode_collision", "word": c,
                               "category": f"撞号：已入册属「{hit['doc']}」({hit['seat']})", "severity": "error",
                               "excerpt": ""})
        elif not hit:
            issues.append({"line": i, "kind": "doccode_cite_unregistered", "word": c,
                           "category": "引用未入册件号（如系新件请先登记）", "severity": "warning",
                           "excerpt": ""})
        # 引用已入册件号：放行
    # 断档提示：同谱系序号跳跃
    for prefix in SERIES:
        nums = []
        for _, c in codes:
            if c.startswith(prefix + "-") and re.match(SERIES[prefix], c):
                tail = re.findall(r"(\d+)$", c)
                if tail:
                    nums.append(int(tail[0]))
        for r in rows:
            if r["code"].startswith(prefix + "-"):
                tail = re.findall(r"(\d+)$", r["code"])
                if tail:
                    nums.append(int(tail[0]))
        if nums and max(nums) - min(nums) + 1 > len(set(nums)) + 1:
            issues.append({"line": 0, "kind": "doccode_gap", "word": prefix,
                           "category": f"{prefix} 谱系序号疑似断档（{min(nums)}..{max(nums)}，建议核对补登）",
                           "severity": "warning", "excerpt": ""})
    if not codes:
        issues.append({"line": 0, "kind": "doccode_absent", "word": "-",
                       "category": "全文零件号（报告类强制配号；简报/草稿豁免）", "severity": "warning",
                       "excerpt": ""})
    return {"codes": sorted(seen_here), "issues": issues, "registry_rows": len(rows)}

def skeleton(path):
    text = open(path, encoding="utf-8").read()
    lines = [l for l in text.split("\n")]
    errs = []
    h1 = [l for l in lines if l.startswith("# ") and not l.startswith("## ")]
    if len(h1) != 1:
        errs.append(f"H1 数量={len(h1)}（应恰为 1）")
    first_nonempty = next((l for l in lines if l.strip()), "")
    if h1 and first_nonempty != h1[0]:
        errs.append("H1 非首个非空行")
    for f in ["文档标识", "版本", "状态", "更新日期", "责任席", "关联锚点"]:
        if f"| {f} |" not in text:
            errs.append(f"文档头缺要素：{f}")
    if not re.search(r"^## (变更记录|CHANGELOG|更新记录)\s*$", text, re.M):
        errs.append("缺变更记录节")
    return errs

# v0.3.0 增量：骨架豁免档。前期简报/过程说明类文书（非双框架正式文书）不强制六要素骨架；
# 豁免清单显式登记于 verifier/v3/verify_goal.py EXEMPT，防例外膨胀。
def _is_exempt(path, exempt_names):
    return os.path.basename(path) in exempt_names

def report(r, sk, dc=None):
    errs = [i for i in r["issues"] if i["severity"] == "error"]
    warns = [i for i in r["issues"] if i["severity"] == "warning"]
    out = [f"预检报告 {r['file']}",
           f"一、术语闸：{'退回' if errs else '通过'}（error={len(errs)} warning={len(warns)}）"]
    for i in r["issues"]:
        out.append(f"  [{i['severity']}] 行{i['line']} {i['category']}：「{i['word']}」｜{i['excerpt']}")
    out.append(f"  链接登记 {r['url_count']} 枚（零改动比对基准）")
    out.append(f"  规范自称在场：{'是' if r['self_reference_ok'] else '否（警告）'}")
    if sk is not None:
        out.append(f"二、骨架闸：{'退回' if sk else '通过'}" + ("" if not sk else "｜" + "；".join(sk)))
    dc_errs = []
    if dc is not None:
        dc_errs = [i for i in dc["issues"] if i["severity"] == "error"]
        dc_warns = [i for i in dc["issues"] if i["severity"] == "warning"]
        out.append(f"三、编码闸：{'退回' if dc_errs else '通过'}"
                   f"（件号 {len(dc['codes'])} 枚入检，台账 {dc['registry_rows']} 行，error={len(dc_errs)} warning={len(dc_warns)}）")
        for c in dc["codes"]:
            out.append(f"  件号登记：{c}")
        for i in dc["issues"]:
            loc = f"行{i['line']} " if i["line"] else ""
            out.append(f"  [{i['severity']}] {loc}{i['category']}：「{i['word']}」")
    out.append("结论：" + ("退回修改" if (errs or sk or dc_errs) else "可过闸（warning 逐条处置后送审）"))
    return "\n".join(out)

def self_test():
    import tempfile, os, hashlib
    global REGISTRY
    good = "# 标题\n\n| 字段 | 内容 |\n|------|------|\n| 文档标识 | T-1 |\n| 版本 | v0.1.0 |\n| 状态 | 草案 |\n| 更新日期 | 2026-10-03 |\n| 责任席 | 本席 |\n| 关联锚点 | 无 |\n\n## 正文\n\n本席载明：指标为三项。\n\n## 变更记录\n\n| 版本 | 日期 | 变更摘要 | 责任席 |\n|------|------|----------|--------|\n| v0.1.0 | 2026-10-03 | 初版 | 本席 |\n"
    bad = "# 标题\n\n我觉得这个方案大概能搞定，变现路径相关等等。\n\n定义为若干指标在一定程度上满足。\n"
    coded = good + "\n件号：GW-DOCCODE-2026-1003-01。\n"
    badcode = good + "\n件号：GW-DOCCODE-20261003-01（日期段超制）与 XX-UNKNOWN-1 并见。\n"
    collide = good + "\n件号：TREE-K3-2026-1003-01。\n"
    unreg = good + "\n件号：GW-NINE-2026-1003-09。\n"
    with tempfile.TemporaryDirectory() as d:
        # 微型台账隔离（自检不触真台账）：c.md 自持 GW 号，other.md 持 TREE 号
        mini = [
            {"seq": 1, "code": "GW-DOCCODE-2026-1003-01", "series": "GW", "doc": "c.md", "seat": "selftest", "date": "2026-10-03", "status": "active"},
            {"seq": 2, "code": "TREE-K3-2026-1003-01", "series": "TREE", "doc": "other.md", "seat": "selftest", "date": "2026-10-03", "status": "active"},
        ]
        prev, reg_lines = "GENESIS", []
        for r in mini:
            core = {k: r[k] for k in ("seq", "code", "series", "doc", "seat", "date", "status")}
            h = hashlib.sha256((json.dumps(core, ensure_ascii=False, separators=(",", ":")) + prev).encode("utf-8")).hexdigest()
            r = dict(r, prev_hash=prev, sha256=h)
            prev = h
            reg_lines.append(json.dumps(r, ensure_ascii=False))
        reg_path = Path(d) / "mini_registry.jsonl"
        reg_path.write_text("\n".join(reg_lines) + "\n", encoding="utf-8")
        old_registry = REGISTRY
        REGISTRY = reg_path
        try:
            gp, bp = os.path.join(d, "g.md"), os.path.join(d, "b.md")
            cp, xp = os.path.join(d, "c.md"), os.path.join(d, "x.md")
            yp, zp = os.path.join(d, "y.md"), os.path.join(d, "z.md")
            open(gp, "w", encoding="utf-8").write(good)
            open(bp, "w", encoding="utf-8").write(bad)
            open(cp, "w", encoding="utf-8").write(coded)
            open(xp, "w", encoding="utf-8").write(badcode)
            open(yp, "w", encoding="utf-8").write(collide)
            open(zp, "w", encoding="utf-8").write(unreg)
            rg, rb = scan(gp), scan(bp)
            assert not [i for i in rg["issues"] if i["severity"] == "error"], f"好件误报: {rg['issues']}"
            assert not skeleton(gp), f"好件骨架误报: {skeleton(gp)}"
            bad_errs = [i for i in rb["issues"] if i["severity"] == "error"]
            assert len(bad_errs) >= 4, f"坏件漏报: {rb['issues']}"
            assert skeleton(bp), "坏件骨架应报错"
            # 编码闸自检：合规自持不报错；超制报语法；声明他件判撞号；未入册检出；无号提示
            dc_good = doccode(cp, doc_id="GW-DOCCODE-2026-1003-01")
            assert not [i for i in dc_good["issues"] if i["severity"] == "error"], f"合规件号误报: {dc_good['issues']}"
            dc_bad = doccode(xp, doc_id="GW-DOCCODE-20261003-01")
            assert any(i["kind"] == "doccode_syntax" for i in dc_bad["issues"]), f"超制件号漏报: {dc_bad['issues']}"
            dc_col = doccode(yp, doc_id="TREE-K3-2026-1003-01")
            assert any(i["kind"] == "doccode_collision" for i in dc_col["issues"]), "声明他件件号应判撞号"
            dc_unr = doccode(zp, doc_id="GW-NINE-2026-1003-09")
            assert any(i["kind"] == "doccode_not_registered" for i in dc_unr["issues"]), "未入册件号应检出"
            dc_none = doccode(gp)
            assert any(i["kind"] == "doccode_absent" for i in dc_none["issues"]), "无号件应出提示"
            # 链接登记自检（v0.2.1）：句读黏连须剥离，登记基准逐字干净
            up = os.path.join(d, "u.md")
            open(up, "w", encoding="utf-8").write(good + "\n见 https://example.com/a。b；甲(https://example.com/c)，乙。《https://example.com/d》\n")
            ru = scan(up)
            got = sorted(u["url"] for u in ru["urls"])
            want = ["https://example.com/a", "https://example.com/c", "https://example.com/d"]
            assert got == want, f"URL 句读黏连未剥离: {got}"
            # 自更新链接自检（v0.3.0）：签名直链出 warning、普通链接不出
            sp = os.path.join(d, "s.md")
            open(sp, "w", encoding="utf-8").write(
                good + "\n附件 https://kss.ksyun.com/x/y.pdf?KSSAccessKeyId=AKLT1&Signature=abc%3D&Expires=1768000000 与 https://example.com/norm\n")
            rs_ = scan(sp)
            hits = [i for i in rs_["issues"] if i["kind"] == "self_refreshing_url"]
            assert len(hits) == 1 and "ksyun" in hits[0]["word"], f"自更新链接漏报/误报: {hits}"
            assert not [i for i in rg["issues"] if i["kind"] == "self_refreshing_url"], "好件不应命中自更新链接"
        finally:
            REGISTRY = old_registry
    print("self-test PASS")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--self-test" in args:
        sys.exit(self_test())
    if not args or args[0].startswith("--"):
        print(__doc__); sys.exit(2)
    path = args[0]
    r = scan(path)
    sk = skeleton(path) if "--skeleton-only" in args or True else None  # 骨架恒检（最小集）
    dc = None
    if "--doccode" in args:
        m = re.search(r"件号[:：]\s*([A-Z][A-Z0-9-]+)", open(path, encoding="utf-8").read())
        dc = doccode(path, doc_id=(m.group(1) if m else None))
    if "--json" in args:
        r["skeleton_errors"] = sk
        if dc is not None:
            r["doccode"] = dc
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(report(r, sk, dc))
    errs = [i for i in r["issues"] if i["severity"] == "error"]
    dc_errs = [i for i in dc["issues"] if i["severity"] == "error"] if dc else []
    sys.exit(1 if errs or sk or dc_errs else 0)
