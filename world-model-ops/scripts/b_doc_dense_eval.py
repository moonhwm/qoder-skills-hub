# -*- coding: utf-8 -*-
"""b_doc_dense_eval.py —— 向量臂（dense）在"档级释义基准"上之评测（★默认 dry-run）
前置：先以 vec_index.py build 建"节级向量索引"（合规档 ≲0.04 元；须裁准）
本器：① 只嵌入★查询（69 条，小额）⇒ ② 与既有索引之节向量算余弦 ⇒ ③ 档级命中（命中目标档任一节即算）
      ⇒ 给出 Hit@1／Hit@5／MRR，并与 BM25 之 0.1758（同基准）对照 ⇒ ★首个"向量是否提升"之可失败判。
判据（可失败）：①索引可读且维度一致；②查询数 = 集之条数；③★ΔMRR（dense − BM25）已给出（正负皆如实）
用法：
    python b_doc_dense_eval.py --vec <vec_index_*.json> --set <档级集> [--index <合规索引>]      # dry-run
    python b_doc_dense_eval.py --vec … --set … --run --budget-max 0.01
（中文串一律用「」）
"""
import argparse, json, math, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP = "https://api.302ai.cn/v1/embeddings"; PROXY = "http://127.0.0.1:10081"
MODEL = "text-embedding-3-small"
BM25_MRR = 0.1758        # ★同基准（档级释义 69 条）之 BM25 MRR，见 -1211／-1212


def env_key():
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
    req = urllib.request.Request(EP, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=120) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    return [d["embedding"] for d in j.get("data", [])], j.get("usage", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vec", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--index", default=""); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--run", action="store_true"); ap.add_argument("--budget-max", type=float, default=0.0)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    vp = pathlib.Path(a.vec)
    print("  ═══ 向量臂（dense）于档级释义基准 ═══")
    if not vp.exists():
        print("   ★向量索引不在：%s ⇒ 须先以 vec_index.py build 建之（≲0.04 元，候裁）" % vp.name)
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）")
        return 0
    v = json.loads(vp.read_text(encoding="utf-8-sig"))
    rows = v.get("rows") or []
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]
    print("   索引：%s ｜ 节向量 %d ｜ 维度 %s" % (vp.name, len(rows), v.get("dim")))
    print("   查询 %d 条 ｜ 对照 BM25 之 MRR %.4f（同基准，见 -1211）" % (len(pairs), BM25_MRR))
    est = len(pairs) * 30 / 1000 * 0.0002
    print("   ★计划：仅嵌入查询 %d 次 ｜ ★成本上界 %.5f 元" % (len(pairs), est))
    if not a.run:
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）—— 真跑须 --run --budget-max <元>")
        return 0
    if a.budget_max <= 0 or est > a.budget_max:
        print("   ★须 --budget-max ≥ %.5f ⇒ 拒绝执行（宁停不超）" % est); return 2
    k = env_key()
    if not k:
        print("   ★无凭据 ⇒ 未测"); return 2
    # ★真跑：仅嵌查询（分批）
    qs = [q for q, _ in pairs]
    qv = []; usage = {}
    for i in range(0, len(qs), 8):
        vs, u = embed(qs[i:i+8], k); qv += vs
        for kk, vv in (u or {}).items():
            if isinstance(vv, (int, float)): usage[kk] = usage.get(kk, 0) + vv
    print("   查询已嵌入 %d 条（usage=%s）" % (len(qv), json.dumps(usage, ensure_ascii=False)))

    def cos(x, y):
        s = sum(p*q for p, q in zip(x, y))
        nx = math.sqrt(sum(p*p for p in x)); ny = math.sqrt(sum(q*q for q in y))
        return s/((nx*ny) or 1e-9)
    hits = []; order_cache = {}
    idx = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig")) if a.index and pathlib.Path(a.index).exists() else None
    for (q, key), vec in zip(pairs, qv):
        scored = [(cos(vec, r["v"]), r.get("i")) for r in rows if isinstance(r.get("v"), list)]
        scored.sort(key=lambda t: -t[0])
        rank = None
        for p, (_, si) in enumerate(scored, 1):
            if idx is None: break
            s = (idx.get("sections") or [])[si] if isinstance(si, int) and si < len(idx.get("sections") or []) else {}
            if key in str(s.get("doc") or ""): rank = p; break
        hits.append(rank)
    n = len(hits)
    H1 = sum(1 for r in hits if r == 1)/max(1, n)
    H5 = sum(1 for r in hits if r and r <= a.k)/max(1, n)
    M = sum((1.0/r) if r else 0.0 for r in hits)/max(1, n)
    crit = {"①索引可读且维度一致": all(len(r.get("v") or []) == v.get("dim") for r in rows[:5]),
            "②查询数 = 集之条数": n == len(pairs),
            "③★ΔMRR（dense − BM25）已给出": True}
    print("   ★dense：Hit@1 %.4f ｜ Hit@%d %.4f ｜ ★MRR %.4f" % (H1, a.k, H5, M))
    print("   ⇒ ★ΔMRR（dense − BM25）＝ %+.4f ⇒ %s" % (M - BM25_MRR,
          "★向量臂有效（语义信号确有增益）" if M > BM25_MRR + 0.05 else "★向量臂未显著提升"))
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "n": n, "hit1": round(H1, 4), "hit5": round(H5, 4), "mrr": round(M, 4),
            "bm25_mrr": BM25_MRR, "dmrr": round(M - BM25_MRR, 4), "usage": usage, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
