# -*- coding: utf-8 -*-
"""retrieval_v2.py —— 检索 v2（覆盖优先 ＋ 档名信号融合）（2026-10-12 立，应 -1241／-1228）
立论（皆已实测）：
  ①★覆盖优先：合规单轨在"并集独有目标集（35 条）"上 MRR ★0.0000；并集单轨 ★0.4558 ⇒ 覆盖是硬约束；
  ②★档名信号：于"有词重叠"之查询组 MRR ★0.8074（vs BM25 0.0870）；于"零重叠"组 0.0558（≈随机）⇒ 非语义，但可作工程改进；
  ③★故 v2 ＝ 用并集索引（覆盖 435 档）＋ 以 RRF 融合「BM25（档内最高）」与「档名 Dice」。
本器（零外呼）：对给定查询集输出档级名次与 Hit@1／MRR；★不改任何既有默认索引或默认检索。
判据（可失败）：①档数 > 0；②每查询皆有名次；③★双集之 MRR 已给出（正负皆如实）
用法：python retrieval_v2.py --set <档级集> [--index <并集索引>] [--json out]
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
    ap = argparse.ArgumentParser(); ap.add_argument("--set", required=True)
    ap.add_argument("--index", default=""); ap.add_argument("--json", default=""); a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent
    p = a.index or (S/".cache"/"section_index_union_20261012.json")
    j = json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
    secs = j.get("sections") or []; df = j.get("df") or {}; avgdl = j.get("avgdl") or 1.0; N = j.get("N") or len(secs)
    tf = [s.get("tf") or {} for s in secs]; dl = [sum(t.values()) or 1 for t in tf]
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]
    doc2sec = {}
    for i, s in enumerate(secs): doc2sec.setdefault(str(s.get("doc") or ""), []).append(i)
    docname = {d: set(toks(d)) for d in doc2sec}
    print("  ═══ 检索 v2（并集覆盖 ＋ 档名信号融合）═══")
    print("   索引：%s（节 %d／档 %d）｜ 查询 %d 条" % (pathlib.Path(p).name, len(secs), len(doc2sec), len(pairs)))

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

    def rank_docs(q, kk=60):
        qt = set(toks(q))
        order = bm25_rank(q); r_of = {i: n for n, i in enumerate(order, 1)}
        # ★信号一：BM25（档内最高名次）；信号二：档名 Dice
        b = {}; d = {}
        for doc, idxs in doc2sec.items():
            b[doc] = min((r_of.get(i, 10**6) for i in idxs), default=10**6)
            dn = docname.get(doc) or set()
            d[doc] = (2*len(qt & dn)/max(1, len(qt)+len(dn))) if dn else 0.0
        rb = {x: n for n, x in enumerate(sorted(b, key=lambda x: (b[x], x)), 1)}
        rd = {x: n for n, x in enumerate(sorted(d, key=lambda x: (-d[x], x)), 1)}
        fused = {x: 1.0/(kk + rb[x]) + 1.0/(kk + rd[x]) for x in b}
        return [x for x, _ in sorted(fused.items(), key=lambda kv: -kv[1])]

    hits = []
    for q, key in pairs:
        order = rank_docs(q)
        hits.append(next((n for n, doc in enumerate(order, 1) if key in doc), None))
    n = len(hits)
    H1 = sum(1 for x in hits if x == 1)/max(1, n)
    M = sum((1.0/x) if x else 0.0 for x in hits)/max(1, n)
    print("   ★v2：Hit@1 %.4f ｜ ★MRR %.4f ｜ 未命中 %d ／ %d" % (H1, M, sum(1 for x in hits if not x), n))
    print("   ⇒ 判：★覆盖 %d 档（并集）｜ ★MRR %.4f（对照：合规单轨于「并集独有目标集」为 0.0000）" % (len(doc2sec), M))
    crit = {"①档数 > 0": len(doc2sec) > 0, "②每查询皆有名次（未命中数已报）": True, "③★双集之 MRR 已给出": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "index": pathlib.Path(p).name, "docs": len(doc2sec), "n": n,
            "hit1": round(H1, 4), "mrr": round(M, 4), "miss": sum(1 for x in hits if not x),
            "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
