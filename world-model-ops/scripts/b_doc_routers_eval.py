# -*- coding: utf-8 -*-
"""b_doc_routers_eval.py —— 在"档级释义基准"上跑融合臂（零外呼）：BM25 vs RRF(BM25 ＋ 字面 bigram 相似)
动机：他席在其（饱和）基准上得"重排 ΔMRR 负"；本席已在"能失败之基准"（档级释义，ΔMRR −0.4459）
     上重问一次：★纯词面之融合（RRF）能否救释义查询？—— 若不能，则证"须真语义（向量／模型）"。
判据（可失败）：①两臂皆可算分；②★RRF 之 MRR 与 BM25 之差已给出（正／负皆须如实）
用法：python b_doc_routers_eval.py --index <合规索引> --set <档级集> [--k 5] [--json out]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, re, sys, time

STOP = set("的 了 与 及 和 是 在 有 为 以 对 之 其 者 等 一 二 三 四 五 六 七 八 九 十 我 他 她 它 你 这 那 不 无 也 就 而 且 或 由 于 从 到 将 被 把 使 让 若 则 因 故 但 并 已 未 可 能 会 应 须 需 要 该 此 本".split())


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t))
    out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return [x for x in out if x and x not in STOP]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--index", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--k", type=int, default=5); ap.add_argument("--json", default="")
    a = ap.parse_args()
    idx = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig"))
    secs = idx.get("sections") or []; df = idx.get("df") or {}
    avgdl = idx.get("avgdl") or 1.0; N = idx.get("N") or len(secs)
    tf = []; dl = []; bags = []
    for s in secs:
        t = s.get("tf") or {}
        tf.append(t); dl.append(sum(t.values()) if t else len(toks(s.get("body") or "")))
        bags.append(set(toks((s.get("head") or "") + " " + (s.get("body") or ""))))
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]

    def bm25_rank(q):
        qt = toks(q); sc = []
        for i in range(len(secs)):
            s = 0.0
            for w in qt:
                f = tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                s += idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * dl[i] / avgdl))
            if s > 0: sc.append((s, i))
        sc.sort(key=lambda t: -t[0]); return [i for _, i in sc]

    def bigram_rank(q):
        """★字面 bigram 相似（与 BM25 独立之第二信号）"""
        qt = set(toks(q)); sc = []
        for i in range(len(secs)):
            b = bags[i]
            if not b or not qt: continue
            j = len(qt & b) / len(qt | b)
            if j > 0: sc.append((j, i))
        sc.sort(key=lambda t: -t[0]); return [i for _, i in sc]

    def rrf(orders, kk=60):
        sc = {}
        for o in orders:
            for p, i in enumerate(o, 1): sc[i] = sc.get(i, 0.0) + 1.0/(kk + p)
        return [i for i, _ in sorted(sc.items(), key=lambda t: -t[1])]

    def ev(rankfn):
        rows = []
        for q, key in pairs:
            tgts = {i for i, s in enumerate(secs) if key in str(s.get("doc") or "")}
            if not tgts: continue
            order = rankfn(q)
            pos = [p for p, i in enumerate(order, 1) if i in tgts]
            rows.append(min(pos) if pos else None)
        H1 = sum(1 for r in rows if r == 1)/max(1, len(rows))
        H5 = sum(1 for r in rows if r and r <= a.k)/max(1, len(rows))
        M = sum((1.0/r) if r else 0.0 for r in rows)/max(1, len(rows))
        return len(rows), H1, H5, M

    n1, h1, h5, m1 = ev(bm25_rank)
    n2, h2, h52, m2 = ev(lambda q: rrf([bm25_rank(q), bigram_rank(q)]))
    crit = {"①两臂皆可算分": n1 > 0 and n2 > 0, "②★RRF 与 BM25 之 Δ 已给出": True}
    print("  ═══ 档级释义基准上之两臂（零外呼）═══")
    print("   查询 %d 条 ｜ 索引节 %d" % (len(pairs), len(secs)))
    print("   ★BM25        ：Hit@1 %.4f ｜ Hit@%d %.4f ｜ ★MRR %.4f" % (h1, a.k, h5, m1))
    print("   ★RRF(BM25＋bigram)：Hit@1 %.4f ｜ Hit@%d %.4f ｜ ★MRR %.4f" % (h2, a.k, h52, m2))
    print("   ⇒ ★ΔMRR（RRF − BM25）＝ %+.4f ⇒ %s" % (m2 - m1,
          "★融合亦救不了释义查询 ⇒ ★须真语义（向量／模型）" if m2 - m1 < 0.03 else "★融合有效"))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "n": n1, "bm25": {"hit1": round(h1,4), "hit5": round(h5,4), "mrr": round(m1,4)},
            "rrf": {"hit1": round(h2,4), "hit5": round(h52,4), "mrr": round(m2,4)},
            "dmrr": round(m2-m1,4), "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
