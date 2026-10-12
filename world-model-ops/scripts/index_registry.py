# -*- coding: utf-8 -*-
"""index_registry.py —— 索引内容指纹登记表（跨档对比之据）
做法：扫描 exp/.cache/ 与 seat/archive/cache/ 之全部索引档 ⇒ 计其"指纹／节数／文档数／tf／件号映射一致性／时效"
      ⇒ 与已录之"评测读数"（按指纹对应）合表 ⇒ ★追加写入 ledger/index_registry.jsonl（★按指纹去重、只增不改）
用法：python index_registry.py [--json out] [--quiet]
（中文串一律用「」）
"""
import argparse, hashlib, json, os, pathlib, re, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
CACHE = SEAT/"exp"/".cache"
ARCH = SEAT/"archive"/"cache"
REG = SEAT/"ledger"/"index_registry.jsonl"

# ★已录之评测读数（按索引指纹；★只记实测，未测者留空）
READINGS = {
    "65d2a9dfaa0c224f": {"档": "旧档（3,126 节；无 tf）", "none_A": 0.801, "none_B": 0.687, "multi_A": 0.407,
                          "multi_B": 0.944, "multi2_B": 0.015, "oracle_B": 0.958, "来源": "-1130／-1131"},
    "eb47856e6cb692ea": {"档": "新档（1,068 节；含 tf）", "none_A": 0.711, "none_B": 0.697, "multi_A": 0.372,
                          "multi_B": 0.870, "multi2_B": 0.050, "oracle_B": 0.892, "来源": "重建后复测（-1133）"},
}

def facts(p):
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    secs = j.get("sections") or []
    if not secs: return None
    docs = {s["doc"] for s in secs}
    m = {}
    for f in EX.glob("*.otl"):
        mm = re.search(r"CAIRN-(\d{1,3})", f.name)
        if mm: m["CAIRN-%s" % mm.group(1)] = f.name.split("_")[0]
    hit = sum(1 for v in m.values() if v in docs)
    newest = max((q.stat().st_mtime for q in EX.glob("*.otl")), default=0)
    return {"name": p.name, "path": str(p), "sha16": hashlib.sha3_256(p.read_bytes()).hexdigest()[:16],
            "sections": len(secs), "docs": len(docs), "tf": ("tf" in secs[0]),
            "map_pct": round(100.0*hit/max(1, len(m)), 1), "mtime": p.stat().st_mtime,
            "lag_min": round(max(0.0, (newest - p.stat().st_mtime)/60.0), 1)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    files = []
    for d in (CACHE, ARCH):
        if d.exists(): files += [q for q in d.glob("section_index*.json")]
    rows = []
    for p in files:
        f = facts(p)
        if not f: continue
        f["readings"] = READINGS.get(f["sha16"], {"档": "未录读数"})
        rows.append(f)
    rows.sort(key=lambda r: -r["mtime"])
    print("  ═══ 索引内容指纹登记表 ｜ 共 %d 档（cache %d ＋ archive %d）═══" % (
        len(rows), len([r for r in rows if r["path"].startswith(str(CACHE))]), len([r for r in rows if r["path"].startswith(str(ARCH))])))
    for r in rows:
        rd = r["readings"]
        print("   %-36s %s ｜ 节 %5d ｜ 文档 %3d ｜ tf %s ｜ 映射 %5.1f%% ｜ 落后 %s 分钟 ｜ %s" % (
            r["name"], r["sha16"], r["sections"], r["docs"], "有" if r["tf"] else "★无", r["map_pct"],
            r["lag_min"], "★已录读数" if "none_B" in rd else "未录"))
        if "none_B" in rd:
            print("      读数：none_A %.3f｜none_B %.3f｜multi_A %.3f｜multi_B ★%.3f｜multi2_B %.3f｜oracle_B %.3f（%s）" % (
                rd["none_A"], rd["none_B"], rd["multi_A"], rd["multi_B"], rd["multi2_B"], rd["oracle_B"], rd["来源"]))
    # ★追加写入（按指纹去重）
    seen = set()
    if REG.exists():
        for l in REG.read_text(encoding="utf-8", errors="replace").splitlines():
            if l.strip():
                try: seen.add(json.loads(l)["sha16"])
                except Exception: pass
    new = 0
    with open(REG, "a", encoding="utf-8", newline="\n") as f:
        for r in rows:
            if r["sha16"] in seen: continue
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), **r}, ensure_ascii=False) + "\n")
            seen.add(r["sha16"])      # ★自纠（2026-10-12）：原先只查历史、未把本批已写者加入 ⇒ 同指纹重复登记
            new += 1
    print("   ⇒ 登记：新增 %d 条（按指纹去重；★只增不改）｜表：%s（共 %d 条）" % (
        new, REG.name, len(seen) + new))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "rows": rows},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
