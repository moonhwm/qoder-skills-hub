# -*- coding: utf-8 -*-
"""wall_coverage.py —— 墙闸覆盖之证（2026-10-12 立）
背景：wall_ledger_v2.jsonl 之语义是"命中流水"（source 为命中者），★不记"接入覆盖" ⇒ 覆盖须另证。
本器给出两证：①标记（各支是否含 ★墙闸）②编译（py_compile 是否通过）；并附"该支在台账中之命中数"。
判据（可失败）：①十一支皆含标记 ②十一支皆编译通过 ③台账中"命中数"仅为参考（不设阈值）
用法：python wall_coverage.py [--json out]
（中文串一律用「」）
"""
import argparse, collections, json, pathlib, py_compile, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EXP = SEAT/"exp"
LEDGER = SEAT/"ledger"/"wall_ledger_v2.jsonl"
TARGETS = ["embed_rerank_302.py", "decision_model_api.py", "wm_create_generic.py", "bailian_probe2.py",
           "semantic_search.py", "ai302_cross_review.py", "exp11_action_legality.py", "recheck_adventure_path.py",
           "search_route.py", "decision_vector_rerank.py", "decision_vector_rerank_v2.py"]


def hits_by_source():
    """★返回 {source: {origin: 计数}}（2026-10-12 加 origin 分读；旧行 origin 记 unknown）"""
    c = {}
    try:
        for l in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
            if not l.strip(): continue
            r = json.loads(l)
            s = str(r.get("source") or "")
            o = str(r.get("origin") or "unknown（旧行无此字段）")
            c.setdefault(s, collections.Counter())[o] += 1
    except Exception:
        pass
    return c


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    hb = hits_by_source()
    print("  ═══ 墙闸覆盖之证 ｜ 十一支 ═══")
    print("   %-32s %-8s %-8s %s" % ("支", "标记", "编译", "台账命中数"))
    marked = compiled = 0
    rows = []
    for f in TARGETS:
        p = EXP/f
        if not p.exists():
            print("   %-32s ★不在" % f); rows.append({"file": f, "marked": None, "compiled": None}); continue
        t = p.read_text(encoding="utf-8", errors="replace")
        mk = t.count("★墙闸")
        try:
            py_compile.compile(str(p), doraise=True); cp = True
        except Exception:
            cp = False
        _d = {}
        for k, cnt in hb.items():
            if k.endswith(f):
                for o, v in cnt.items(): _d[o] = _d.get(o, 0) + v
        n = sum(_d.values())
        origin_split = dict(_d)
        marked += 1 if mk > 0 else 0
        compiled += 1 if cp else 0
        rows.append({"file": f, "marked": mk, "compiled": cp, "hits": n, "origin_split": origin_split})
        print("   %-32s %-8s %-8s %s" % (f, ("%d 处" % mk) if mk else "★无", "✓" if cp else "★失败", (json.dumps(origin_split, ensure_ascii=False) if origin_split else "0")))
    crit = {"①十一支皆含★墙闸标记": marked == len(TARGETS),
            "②十一支皆编译通过": compiled == len(TARGETS),
            "③台账命中数为参考（不设阈值）": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 汇总：标记 %d/%d ｜ 编译 %d/%d" % (marked, len(TARGETS), compiled, len(TARGETS)))
    print("   ★注：台账命中数之语义是「命中流水」★非「接入覆盖」⇒ 二者须分读（2026-10-12 明）")
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "targets": len(TARGETS), "marked": marked,
           "compiled": compiled, "rows": rows, "criteria": crit,
           "note": "★覆盖以标记＋编译为证；台账命中数按 origin 分读（runtime／scan／unknown）"}
    if a.json: pathlib.Path(a.json).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
