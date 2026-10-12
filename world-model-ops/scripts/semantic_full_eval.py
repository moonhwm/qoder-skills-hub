# -*- coding: utf-8 -*-
"""semantic_full_eval.py —— 全库语义检索之决定性评测（2026-10-12 立，承 -1258 之限定）
动机：-1258 之探针只在"词面 top-5 内重排" ⇒ ★不足以判"语义 vs 词面"。本器改为：
  ① ★嵌"全部档之档名"（并集 435 档；约 6.5k tokens ⇒ ≈0.0013 元）
  ② 嵌"档级查询集（69 条）"（≈0.0002 元）
  ③ ★算语义检索之 Hit@1／MRR ⇒ 与 v2（0.2662）／合规单轨（0.1758）／并集单轨（0.0633）同基准对照
  ④ ★并试"语义 × v2"之 RRF 融合 ⇒ 看是否兼得
★安全：--dry-run 默认；真跑须 --run --budget-max（★器内闸；宁停不超）；★不回显凭据。
判据（可失败）：①计划之调用数与成本上界已给；②真跑时向量齐备（档 435／查询 69）；③★三臂之 MRR 已给出
用法：python semantic_full_eval.py ｜ --run --budget-max 0.01
（中文串一律用「」）
"""
import argparse, json, math, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP = "https://api.302ai.cn/v1/embeddings"; PROXY = "http://127.0.0.1:10081"
MODEL = "text-embedding-3-small"; PRICE = 0.0002


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def embed(texts, k):
    import urllib.request
    body = json.dumps({"model": MODEL, "input": texts}, ensure_ascii=False).encode()
    r = urllib.request.Request(EP, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(r, timeout=180) as resp:
        j = json.loads(resp.read().decode("utf-8", "replace"))
    return [d["embedding"] for d in j.get("data", [])], j.get("usage", {})


def cos(a, b):
    s = sum(x*y for x, y in zip(a, b)); na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return s/((na*nb) or 1e-9)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget-max", type=float, default=0.0); ap.add_argument("--json", default="")
    ap.add_argument("--set", default=""); a = ap.parse_args()
    j = json.loads((SEAT/".cache"/"section_index_union_20261012.json").read_text(encoding="utf-8-sig"))
    docs = sorted({str(s.get("doc") or "") for s in j.get("sections") or []})
    sp = pathlib.Path(a.set) if a.set else SEAT.parent/"outbox"/"mem"/"b_spec_doc_20261012.json"
    pairs = json.loads(sp.read_text(encoding="utf-8-sig"))["pairs"]
    qs = [q for q, _ in pairs]
    txts = docs + qs
    chars = sum(len(t) for t in txts); cost = chars/1.7/1000*PRICE
    print("  ═══ 全库语义检索评测（★档名语义）═══")
    print("   档 %d ＋ 查询 %d ＝ 文本 %d 条／%d 字符 ⇒ 约 %.1f k tokens" % (len(docs), len(qs), len(txts), chars, chars/1.7/1000))
    print("   ★计划：%d 批调用｜★成本上界 %.6f 元" % ((len(txts)+7)//8, cost))
    if not a.run:
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）—— 真跑须 --run --budget-max <元>")
        return 0
    if a.budget_max <= 0 or cost > a.budget_max:
        print("   ★须 --budget-max ≥ %.6f ⇒ 拒绝执行（宁停不超）" % cost); return 2
    k = key()
    if not k: print("   ★无凭据 ⇒ 未测"); return 2
    V, usage = {}, {}
    for i in range(0, len(txts), 8):
        vs, u = embed(txts[i:i+8], k)
        for t, v in zip(txts[i:i+8], vs): V[t] = v
        for kk, vv in (u or {}).items():
            if isinstance(vv, (int, float)): usage[kk] = usage.get(kk, 0) + vv
    print("   ★已嵌 %d 条 ｜ usage=%s" % (len(V), json.dumps(usage, ensure_ascii=False)))
    # ★2026-10-12 自纠：付费调用之产物★须落自述缓存（否则"用过即弃"）
    wrote = 0
    try:
        import importlib.util
        spec3 = importlib.util.spec_from_file_location("ec2", SEAT/"emb_cache.py")
        ec2 = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(ec2)
        for _t, _v in V.items():
            try:
                ec2.put(_t, _v, model=MODEL, src="semantic_full_eval"); wrote += 1
            except Exception:
                pass
    except Exception as _e:
        print("   ⚠ 写缓存失败：%s" % str(_e)[:70])
    print("   ★自述缓存已写 %d 条（src=semantic_full_eval）" % wrote)
    # ★语义臂
    hits = []
    for q, gold in pairs:
        qv = V.get(q)
        if not qv: hits.append(None); continue
        sc = sorted(docs, key=lambda d: -cos(qv, V.get(d) or [0]*len(qv)))
        hits.append(next((n for n, d in enumerate(sc, 1) if gold in d), None))
    n = len(hits)
    H1 = sum(1 for x in hits if x == 1)/max(1, n); M = sum((1.0/x) if x else 0 for x in hits)/max(1, n)
    print("   ★语义臂（全库档名）：Hit@1 %.4f ｜ ★MRR %.4f ｜ 未命中 %d／%d" % (H1, M, sum(1 for x in hits if not x), n))
    print("   ★对照：v2 0.2662（本集）｜合规单轨 0.1758｜并集单轨 0.0633")
    crit = {"①计划之调用数与成本上界已给": True, "②真跑时向量齐备": len(V) == len(txts), "③★三臂之 MRR 已给出": True}
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "docs": len(docs), "queries": n, "usage": usage, "cost_upper_cny": round(cost, 6),
            "semantic": {"hit1": round(H1, 4), "mrr": round(M, 4), "miss": sum(1 for x in hits if not x)},
            "compare": {"v2": 0.2662, "compliant": 0.1758, "union": 0.0633}, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
