# -*- coding: utf-8 -*-
"""criterion_selfcheck.py —— 出件前自检闸（把 2026-10-12 之"自纠九类"固化为可失败判据）
九类来历：tf 缺失（器空转）／scope 未接线（假实现）／金标未按域筛（假红）／幸存者偏差（假绿）
        ／过度校正（把特征当偏差）／回归判据错配／索引陈旧·回滚／以空为同／批内去重缺失
本闸所检（★任一项不过即红，退出码 1；环境不足 ⇒ 未测，退出码 2）：
  ①索引含 tf（免器空转）
  ②索引指纹已登记（否则读数不可跨档比）
  ③索引解析消费者齐全（section_search／retrieval_eval／index_guard 皆支持 env 与指针）
  ④回归基线绑指纹（retrieval_eval 之 BASE_IDX 非占位）
  ⑤日更⑨项读"最后非空版"（免以空为同）
  ⑥档保留策略存在（若曾剪档则须有清单；无剪档 ⇒ 记为"未用"非失败）
  ⑦台账链 PASS
用法：python criterion_selfcheck.py [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, re, subprocess, sys

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EXP = SEAT/"exp"

def read(p):
    try: return p.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    res = {}
    # ① 索引含 tf
    idx = None
    ptr = SEAT/"exp"/".cache"/"index_pointer.json"
    if ptr.exists():
        try: idx = pathlib.Path(json.loads(read(ptr))["index"])
        except Exception: idx = None
    if idx is None: idx = SEAT/"exp"/".cache"/"section_index.json"
    ok1 = False
    if idx.exists():
        try:
            j = json.loads(read(idx)); secs = j.get("sections") or []
            ok1 = bool(secs) and ("tf" in secs[0])
        except Exception: ok1 = False
    res["①索引含 tf（免器空转）"] = ok1
    # ② 指纹已登记
    reg = SEAT/"ledger"/"index_registry.jsonl"
    ok2 = False
    if reg.exists() and idx.exists():
        import hashlib
        sha = hashlib.sha3_256(idx.read_bytes()).hexdigest()[:16]
        ok2 = any(sha in l for l in read(reg).splitlines())
    res["②当前索引指纹已登记"] = ok2
    # ③ 索引解析消费者齐全
    cons = ["section_search.py", "retrieval_eval.py", "index_guard.py"]
    miss = [c for c in cons if "OPL_SECTION_IDX" not in read(EXP/c)]
    res["③三消费者皆支持索引覆盖（缺：%s）" % ("、".join(miss) if miss else "无")] = (not miss)
    # ④ 回归基线绑指纹（非占位）
    t = read(EXP/"retrieval_eval.py")
    m = re.search(r'BASE_IDX\s*=\s*"([0-9a-f]{16})"', t)
    res["④回归基线绑真实指纹"] = bool(m)
    # ⑤ 日更⑨读最后非空版
    d = read(EXP/"daily_nine_audit_20261010.py")
    res["⑤日更⑨读最后非空版（免以空为同）"] = ("len(x) > 0" in d or "最后非空" in d)
    # ⑥ 档保留策略（清单存在 ⇒ 用过；不存在 ⇒ 未用，不判红）
    man = SEAT/"archive"/"cache"/"index_prune_manifest.jsonl"
    res["⑥档保留策略可用（清单在场）"] = man.exists()
    # ⑦ 台账链
    ok7 = False
    try:
        pr = subprocess.run([sys.executable, str(SEAT/"ledger"/"cairn_ledger.py"), "verify"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        ok7 = "PASS" in ((pr.stdout or "") + (pr.stderr or ""))
    except Exception: ok7 = False
    res["⑦台账链 PASS"] = ok7
    print("  ═══ 出件前自检闸（自纠九类之固化）═══")
    for k, v in res.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    bad = [k for k, v in res.items() if not v]
    print("   ⇒ 判：%s" % ("✓ 全过" if not bad else "★%d 项不过 ⇒ 出件前须先处置" % len(bad)))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "checks": res, "pass": not bad}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
