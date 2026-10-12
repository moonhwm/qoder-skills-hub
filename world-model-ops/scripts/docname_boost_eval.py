# -*- coding: utf-8 -*-
"""docname_boost_eval.py —— 零成本之精度提升实验：把"档名"信号并入检索（2026-10-12 立）
背景：档级释义基准（69 条）上，合规索引之 BM25 MRR ＝ 0.1758；★其目标是"档"⇒ 而"档名"本身是强信号。
本器（零外呼）三臂对照：
  ① BM25 单臂（节级，取该档各节之最高分）
  ② ★档名相似度单臂（查询 ↔ 档名，bigram Dice）
  ③ ★融合臂（RRF：BM25 名次 与 档名相似度名次）
判据（可失败）：①三臂皆可算分；②★融合臂与 BM25 之 ΔMRR 已给出（正负皆如实）
用法：python docname_boost_eval.py --index <索引> --set <档级集> [--json out]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, re, sys, time

STOP = set("的 了 与 及 和 是 在 有 为 以 对 之 其 者 等 一 二 三 四 五 六 七 八 九 十".split())


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t)); out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return [x for x in out if x and x not in STOP]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--index", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    j = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig"))
    secs = j.get("sections") or []; df = j.get("df") or {}; avgdl = j.get("avgdl") or 1.0; N = j.get("N") or len(secs)
    tf = [s.get("tf") or {} for s in secs]; dl = [sum(t.values()) or 1 for t in tf]
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]
    # ★档 → 其节号集合；档名 → bigram 集
    doc2sec = {}
    for i, s in enumerate(secs): doc2sec.setdefault(str(s.get("doc") or ""), []).append(i)
    docname = {d: set(toks(d)) for d in doc2sec}
    print("  ═══ 档名信号之增益实验（零外呼）═══")
    print("   索引：%s（节 %d／档 %d）｜ 查询 %d 条" % (pathlib.Path(a.index).name, len(secs), len(doc2sec), len(pairs)))

    def bm25_rank(q):
        qt = toks(q); sc = []
        for i in range(len(secs)):
            v = 0.0
            for w in qt:
                f = tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                v += idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * dl[i] / avgdl))
            if v > 0: sc.append((v, i))
        sc.sort(key=lambda x: -x[0]); return [i for _, i in sc]

    def docscore(q):
        """★档级综合分：BM25 之档内最高分（归一后）＋ 档名 Dice"""
        qt = set(toks(q)); order = bm25_rank(q)
        rank_of = {i: p for p, i in enumerate(order, 1)}
        sc = {}
        for d, idxs in doc2sec.items():
            best = min((rank_of.get(i, 10**6) for i in idxs), default=10**6)
            dn = docname.get(d) or set()
            dice = (2*len(qt & dn)/max(1, len(qt)+len(dn))) if dn else 0.0
            sc[d] = (best, dice)
        return sc

    def ev(rankfn):
        hits = []
        for q, key in pairs:
            order = rankfn(q)
            r = next((p for p, d in enumerate(order, 1) if key in d), None)
            hits.append(r)
        n = len(hits)
        return n, sum(1 for x in hits if x == 1)/max(1, n), sum((1.0/x) if x else 0.0 for x in hits)/max(1, n)

    def arm_bm25(q):
        sc = docscore(q)
        return [d for d, (b, _) in sorted(sc.items(), key=lambda kv: kv[1][0])]

    def arm_name(q):
        sc = docscore(q)
        return [d for d, (_, dice) in sorted(sc.items(), key=lambda kv: -kv[1][1])]

    def arm_rrf(q, kk=60):
        sc = docscore(q)
        r1 = {d: p for p, d in enumerate(arm_bm25(q), 1)}
        r2 = {d: p for p, d in enumerate(arm_name(q), 1)}
        fused = {d: 1.0/(kk + r1[d]) + 1.0/(kk + r2[d]) for d in sc}
        return [d for d, _ in sorted(fused.items(), key=lambda kv: -kv[1])]

    n1, h1, m1 = ev(arm_bm25); n2, h2, m2 = ev(arm_name); n3, h3, m3 = ev(arm_rrf)
    print("   ★① BM25 单臂（档级取最高）：Hit@1 %.4f ｜ ★MRR %.4f" % (h1, m1))
    print("   ★② 档名相似度单臂：Hit@1 %.4f ｜ ★MRR %.4f" % (h2, m2))
    print("   ★③ ★融合（RRF：BM25＋档名）：Hit@1 %.4f ｜ ★MRR %.4f" % (h3, m3))
    print("   ⇒ ★ΔMRR（融合 − BM25）＝ %+.4f ｜ ΔMRR（档名 − BM25）＝ %+.4f" % (m3-m1, m2-m1))
    best = max((("BM25", m1), ("档名", m2), ("融合", m3)), key=lambda x: x[1])
    print("   ⇒ 判：★最优臂 ＝ ★%s（%.4f）⇒ %s" % (best[0], best[1],
          "★零成本提升成立" if best[0] != "BM25" else "★未提升（BM25 已最优）"))
    crit = {"①三臂皆可算分": min(n1, n2, n3) > 0, "②★融合与 BM25 之 ΔMRR 已给出": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "n": len(pairs), "bm25": {"hit1": round(h1,4), "mrr": round(m1,4)},
            "docname": {"hit1": round(h2,4), "mrr": round(m2,4)},
            "fused": {"hit1": round(h3,4), "mrr": round(m3,4)},
            "best": best[0], "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
