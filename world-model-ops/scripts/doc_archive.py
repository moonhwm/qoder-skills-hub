# -*- coding: utf-8 -*-
"""文档结构化档案器（可微可导）
可微：正文按"标题分节"切片，每节独立哈希 ⇒ 任何变动定位到节级
可导：manifest 记全史（版本／时间／哈希／字数／节数）＋分节索引 ⇒ 可追溯、可复算
用法：python doc_archive.py [--notify]
（引号一律用「」）
"""
import hashlib, json, pathlib, re, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# ★2026-10-12 参数卫生（自纠）：本器原无参数解析 ⇒ ★任何参数（含 --help／-h）皆被忽略而主流程照跑
#   ⇒ 我曾以 `--help` 探其用法，★竟真跑了一次复拉（-1279 之记载）⇒ 今补：-h／--help 只示帮助，--dry-run 只示计划
if any(x in ("-h", "--help") for x in sys.argv):
    print("用法：python doc_archive.py [--notify] ｜ --dry-run（只示计划，不拉取）")
    print("  ★注意：本器会真拉取两档（outline／polish）并落 archive/docs；--help 只示帮助，不拉取。")
    sys.exit(0)
if "--dry-run" in sys.argv:
    print("★dry-run：将拉取两档（outline、polish）并写 archive/docs；★本次不拉取、不落盘。")
    sys.exit(0)
HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
ARCH = SEAT/"archive"/"docs"
ARCH.mkdir(parents=True, exist_ok=True)
CLI = HOME/".kimi-work"/"bin"/"kdocs-cli.exe"

DOCS = [
    {"key": "outline", "link_id": "ci2ybbMcccFi", "title": "OpenPlanLink全局声明与Agent-to-Agent网络建设纲要"},
    {"key": "polish", "link_id": "cubofOPoRdSw", "title": "2026-9-25-OpenPlanLink 润色-1 (3)"},
    # ★2026-10-12 加（应 -1307 之果）：Re0 之两件经 drive list-latest-items 反查所得
    #   ★润色-1 之 .otl 形态（205 节，粒度更细）；★其与 polish（.docx 版）为同一文档之两形态（归一后差 4.4%）
    {"key": "polish_otl", "link_id": "csiE4H0dSPh9", "title": "2026-9-25-OpenPlanLink 润色-1 (3).otl（Re0 指向）"},
]


def pull(link_id):
    p = subprocess.run([str(CLI), "drive", "read-file", "--args", json.dumps({"link_id": link_id})],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    out = (p.stdout or "") + (p.stderr or "")
    i = out.find("{")
    if i < 0:
        return None, {"err": "无 JSON", "head": out[:160]}
    try:
        j, _ = json.JSONDecoder().raw_decode(out[i:])
    except Exception as e:
        return None, {"err": str(e)[:90]}
    d = j.get("data") or {}
    return d.get("content", ""), {"code": j.get("code"), "format": d.get("content_format"),
                                  "file_id": d.get("file_id"), "drive_id": d.get("drive_id"), "name": d.get("name")}


def sha(t, n=24):
    return hashlib.sha3_512(t.encode("utf-8")).hexdigest()[:n]


def sections(md):
    """按标题切节：返回 [(标题路径, 正文)]"""
    out, cur, buf = [], "(前言)", []
    for line in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if m:
            out.append((cur, "\n".join(buf).strip())); cur = m.group(2).strip(); buf = [line]
        else:
            buf.append(line)
    out.append((cur, "\n".join(buf).strip()))
    return [(t, b) for t, b in out if b.strip()]


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


IDX = ARCH/"index.json"
manifest = load(IDX, {})

report = []
changed_any = False
for d in DOCS:
    content, meta = pull(d["link_id"])
    if content is None:
        report.append((d["key"], "拉取失败", meta)); continue
    h = sha(content)
    secs = sections(content)
    sec_idx = {"%04d|%s" % (i, t): sha(b) for i, (t, b) in enumerate(secs)}   # ★键加序号：同名标题不再互相覆盖
    m = manifest.setdefault(d["key"], {"link_id": d["link_id"], "title": d["title"], "history": []})
    prev = m["history"][-1] if m["history"] else None
    changed = (prev is None) or (prev["hash"] != h)
    # 分节级差异（可微）
    diff = {"added": [], "removed": [], "changed": []}
    if prev:
        old = load(ARCH/d["key"]/("sections_%s.json" % prev["ver"]), {})
        for t in sec_idx:
            if t not in old: diff["added"].append(t)
            elif old[t] != sec_idx[t]: diff["changed"].append(t)
        for t in old:
            if t not in sec_idx: diff["removed"].append(t)
    ver = time.strftime("%Y%m%d_%H%M")
    vd = ARCH/d["key"]; vd.mkdir(parents=True, exist_ok=True)
    (vd/("v_%s.md" % ver)).write_text(content, encoding="utf-8", newline="\n")
    (vd/("sections_%s.json" % ver)).write_text(json.dumps(sec_idx, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    ent = {"ver": ver, "ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "hash": h,
           "chars": len(content), "lines": len(content.splitlines()), "sections": len(secs),
           "file_id": meta.get("file_id"), "drive_id": meta.get("drive_id"),
           "changed": changed, "diff": diff if prev else None}
    m["history"].append(ent)
    m["latest"] = {"hash": h, "chars": len(content), "sections": len(secs), "ver": ver}
    if changed: changed_any = True
    print("  ▶ %-8s %s" % (d["key"], d["title"][:40]))
    print("     拉取：code=%s ｜ %d 字 ｜ %d 行 ｜ %d 节 ｜ sha3-24=%s" % (meta.get("code"), len(content), len(content.splitlines()), len(secs), h))
    if prev:
        print("     vs 上版（%s）：%s ｜ 节级差异 新增 %d／删除 %d／变动 %d" % (
            prev["ver"], "★有变更" if changed else "无变更", len(diff["added"]), len(diff["removed"]), len(diff["changed"])))
        for t in diff["changed"][:6]: print("        ～ " + t[:70])
        for t in diff["added"][:4]: print("        ＋ " + t[:70])
        for t in diff["removed"][:4]: print("        － " + t[:70])
    else:
        print("     ★首建（无上版可比）")
    report.append((d["key"], "有变更" if changed else "无变更", ent))

manifest["_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S+0800")
manifest["_note"] = "可微（节级哈希）可导（全史 manifest）；拉取工具 kdocs-cli v2.6.13；凭据零落盘"
IDX.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\n  ═══ 档案 manifest ═══")
print("   路径：%s（%.1f KB）｜ 文档 %d 件" % (IDX, IDX.stat().st_size/1024, len(DOCS)))
for k, v in manifest.items():
    if k.startswith("_"): continue
    print("   %-8s 版本 %d ｜ 最新 %s（%d 字／%d 节）" % (k, len(v["history"]), v["latest"]["ver"][:8], v["latest"]["chars"], v["latest"]["sections"]))

if changed_any and "--notify" in sys.argv:
    nd = SEAT/"outbox"/"notify"; nd.mkdir(parents=True, exist_ok=True)
    nf = nd/("doc_update_%s.md" % time.strftime("%Y%m%d_%H%M"))
    lines = ["# 文档更新通知（%s）" % time.strftime("%Y-%m-%d %H:%M"), "",
             "★本轮检出**变更**之文档：", ""]
    for k, st, ent in report:
        if st == "有变更":
            lines.append("- **%s**（%s）⇒ %s ｜ %d 字／%d 节 ｜ 节级差异 新增 %d／删除 %d／变动 %d" % (
                k, ent["ver"], ent["hash"], ent["chars"], ent["sections"],
                len((ent["diff"] or {}).get("added", [])), len((ent["diff"] or {}).get("removed", [])),
                len((ent["diff"] or {}).get("changed", []))))
    lines += ["", "档案：`%s`" % IDX]
    nf.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n  ★ 已写通知：%s" % nf.name)
