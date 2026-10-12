# -*- coding: utf-8 -*-
"""index_guard.py —— 索引陈旧检测（应 2026-10-12 之发现：旧索引 3,126 节／无 tf／不含今日件 ⇒ 映射一致性仅 47%）
四项判据（★任一项不过即红，退出码 1；环境不足 ⇒ 未测，退出码 2）：
  ①内容指纹在场：索引可读且含 sections
  ②tf 在场：sections 含 tf 字段（否则 BM25／余弦会全打 0 分 ⇒ 器空转）
  ③件号映射一致性 ≥95%：扫交换区文件名建 件号↔doc 标题 映射，核其在索引 doc 中之命中率
  ④时效：索引 mtime 不早于"最新 .otl 件"之 mtime（陈旧即红）
用法：python index_guard.py [--index <path>] [--rebuild] [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
DEF_IDX = SEAT/"exp"/".cache"/"section_index.json"

def run(a):
    # ★索引解析（2026-10-12 修）：①env OPL_SECTION_IDX ②★指针文件 index_pointer.json ③默认档
    #   —— 原先本器未读指针 ⇒ 切换后它仍报旧档（★"加了全局解析却未逐一接入消费者"之又一例）
    if a.index:
        idx, src = pathlib.Path(a.index), "arg"
    elif os.environ.get("OPL_SECTION_IDX"):
        idx, src = pathlib.Path(os.environ["OPL_SECTION_IDX"]), "env"
    elif (SEAT/"exp"/".cache"/"index_pointer.json").exists():
        try:
            _d = json.loads((SEAT/"exp"/".cache"/"index_pointer.json").read_text(encoding="utf-8"))
            idx, src = pathlib.Path(_d["index"]), "pointer"
        except Exception:
            idx, src = DEF_IDX, "default"
    else:
        idx, src = DEF_IDX, "default"
    print("  ═══ 索引陈旧检测 ｜ %s（来源 %s）═══" % (idx.name, src))
    if not idx.exists():
        print("   ★索引不在 ⇒ 未测（环境不足；退出码 2）"); return 2
    try:
        j = json.loads(idx.read_text(encoding="utf-8"))
    except Exception as e:
        print("   ★索引不可读：%s ⇒ 未测（退出码 2）" % str(e)[:60]); return 2
    secs = j.get("sections") or []
    sha16 = hashlib.sha3_256(idx.read_bytes()).hexdigest()[:16]
    has_tf = bool(secs) and ("tf" in secs[0])
    docs = {s["doc"] for s in secs}
    m, hit = {}, 0
    for f in EX.glob("*.otl"):
        mm = re.search(r"CAIRN-(\d{1,3})", f.name)
        if mm: m["CAIRN-%s" % mm.group(1)] = f.name.split("_")[0]
    hit = sum(1 for v in m.values() if v in docs)
    cons = 100.0*hit/max(1, len(m))
    newest = max((p.stat().st_mtime for p in EX.glob("*.otl")), default=0)
    idx_mt = idx.stat().st_mtime
    # ★时效容差（2026-10-12 修）：只要我持续产出，索引必落后于"最新件"⇒ 无容差则日更永红
    #   ⇒ 改为"落后不超过 tolerance 分钟"（默认 30）；并打印落后分钟数
    lag_min = (newest - idx_mt)/60.0
    fresh = lag_min <= a.tolerance
    print("   节 %d ｜ 文档 %d ｜ 指纹 %s ｜ tf %s" % (len(secs), len(docs), sha16, "有" if has_tf else "★无"))
    print("   件号映射 %d 条 ⇒ 命中 %d 条（★%.0f%%；阈值 95%%）" % (len(m), hit, cons))
    print("   时效：索引 %s ｜ 最新件 %s ⇒ 落后 %.0f 分钟（容差 %d）⇒ %s" % (
        time.strftime("%m-%d %H:%M", time.localtime(idx_mt)), time.strftime("%m-%d %H:%M", time.localtime(newest)),
        max(0.0, lag_min), a.tolerance, "✓ 在容差内" if fresh else "★超出容差（陈旧）"))
    crit = {"①索引可读且含 sections": len(secs) > 0, "②tf 在场（免器空转）": has_tf,
            "③件号映射一致性 ≥95%%（现 %.0f%%）" % cons: cons >= 95.0,
            "④索引落后 ≤%d 分钟（现 %.0f 分钟）" % (a.tolerance, max(0.0, lag_min)): fresh}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"index": idx.name, "sha16": sha16, "sections": len(secs),
            "docs": len(docs), "has_tf": has_tf, "map_total": len(m), "map_hit": hit, "map_consistency_pct": round(cons, 2),
            "index_mtime": idx_mt, "newest_artifact_mtime": newest, "fresh": fresh, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    ok = all(crit.values())
    if not ok and a.rebuild:
        out = SEAT/"exp"/".cache"/("section_index_%s.json" % time.strftime("%Y%m%d_%H%M"))
        env = dict(os.environ); env["OPL_SECTION_IDX"] = str(out)
        print("   → 触发重建：%s" % out.name)
        pr = subprocess.run([sys.executable, str(SEAT/"exp"/"section_search.py"), "--build"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        for l in ((pr.stdout or "") + (pr.stderr or "")).splitlines()[-2:]: print("     " + l.strip()[:100])
        print("     ★据以检索须设 OPL_SECTION_IDX=%s" % out.name)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(); ap.add_argument("--index", default=""); ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--json", default="")
    ap.add_argument("--tolerance", type=int, default=30)   # ★时效容差（分钟）
    sys.exit(run(ap.parse_args()))
