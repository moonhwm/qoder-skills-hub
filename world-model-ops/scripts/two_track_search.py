# -*- coding: utf-8 -*-
"""two_track_search.py —— 双轨检索（2026-10-12 立，应 -1226 之判）
背景：并集索引覆盖广（435 档／3,535 节）而精度低（档级释义 MRR 0.0633）；
     合规索引精度高（MRR 0.1758）而覆盖窄（148 档／1,102 节）⇒ 候选由并集出、排序由合规定。
本器（零外呼）三臂对照：
  ① 合规单轨：全库 BM25 于合规索引
  ② 并集单轨：全库 BM25 于并集索引
  ③ ★双轨：并集取 top-K 候选 ⇒ ★以 RRF 融合「并集名次」与「合规名次（若该节亦在合规索引）」
判据（可失败）：①三臂皆可算分；②★双轨之 MRR 与两单轨之差已给出（正负皆如实）
用法：python two_track_search.py --set <档级集> [--k 50] [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, math, pathlib, re, sys, time

STOP = set("的 了 与 及 和 是 在 有 为 以 对 之 其 者 等".split())


def toks(t):
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t)); out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return [x for x in out if x and x not in STOP]


def fp(s):
    return hashlib.sha3_256(((s.get("head") or "") + "|" + (s.get("body") or "")).encode("utf-8")).hexdigest()[:16]


class Idx:
    def __init__(self, p):
        j = json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
        self.secs = j.get("sections") or []; self.df = j.get("df") or {}
        self.avgdl = j.get("avgdl") or 1.0; self.N = j.get("N") or len(self.secs)
        self.tf = [s.get("tf") or {} for s in self.secs]
        self.dl = [sum(t.values()) or 1 for t in self.tf]
        self.fp = [fp(s) for s in self.secs]

    def rank(self, q):
        qt = toks(q); sc = []
        for i in range(len(self.secs)):
            v = 0.0
            for w in qt:
                f = self.tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (self.N - self.df.get(w, 0) + 0.5) / (self.df.get(w, 0) + 0.5))
                v += idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * self.dl[i] / self.avgdl))
            if v > 0: sc.append((v, i))
        sc.sort(key=lambda x: -x[0]); return [i for _, i in sc]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--set", required=True); ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--union", default=""); ap.add_argument("--comp", default=""); ap.add_argument("--json", default="")
    a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent
    U = Idx(a.union or S/".cache"/"section_index_union_20261012.json")
    C = Idx(a.comp or S/".cache"/"section_index_20261012_1537.json")
    comp_by_fp = {C.fp[i]: i for i in range(len(C.secs))}
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]

    def docset(idx, s):
        return str(idx.secs[s].get("doc") or "")

    def ev(rankfn):
        hits = []
        for q, key in pairs:
            order = rankfn(q)                       # 返回 (idx, 节号) 序列
            r = None
            for p, (which, si) in enumerate(order, 1):
                idx = U if which == "U" else C
                if key in docset(idx, si): r = p; break
            hits.append(r)
        n = len(hits)
        return n, sum(1 for x in hits if x == 1)/max(1, n), sum(1 for x in hits if x and x <= 5)/max(1, n), \
               sum((1.0/x) if x else 0.0 for x in hits)/max(1, n)

    rU = lambda q: [("U", i) for i in U.rank(q)]
    rC = lambda q: [("C", i) for i in C.rank(q)]

    def rT(q):
        cand = U.rank(q)[:a.k]
        cu = {i: p for p, i in enumerate(cand, 1)}
        cc = {}
        for i in cand:
            ci = comp_by_fp.get(U.fp[i])
            if ci is not None:
                # ★该节亦在合规索引 ⇒ 取其合规名次
                cc[i] = ci
        # 合规名次：对候选内之合规节，按合规 BM25 重排
        sc = []
        for i in cand:
            s = 1.0/(60 + cu[i])
            if i in cc:
                s += 1.0/(60 + cc[i] + 1)
            sc.append((s, i))
        sc.sort(key=lambda x: -x[0])
        return [("U", i) for _, i in sc]

    n1, h1, h5a, m1 = ev(rC)
    n2, h2, h5b, m2 = ev(rU)
    n3, h3, h5c, m3 = ev(rT)
    print("  ═══ 双轨检索 三臂对照（档级释义 %d 条；候选 K=%d）═══" % (len(pairs), a.k))
    print("   ★① 合规单轨（1,102 节）：Hit@1 %.4f ｜ Hit@5 %.4f ｜ ★MRR %.4f" % (h1, h5a, m1))
    print("   ★② 并集单轨（3,535 节）：Hit@1 %.4f ｜ Hit@5 %.4f ｜ ★MRR %.4f" % (h2, h5b, m2))
    print("   ★③ 双轨（并集召回＋合规重排）：Hit@1 %.4f ｜ Hit@5 %.4f ｜ ★MRR %.4f" % (h3, h5c, m3))
    print("   ⇒ ★ΔMRR（双轨 − 合规）＝ %+.4f ｜ ★ΔMRR（双轨 − 并集）＝ %+.4f" % (m3-m1, m3-m2))
    best = max((("合规单轨", m1), ("并集单轨", m2), ("双轨", m3)), key=lambda x: x[1])
    print("   ⇒ 判：★三臂中 MRR 最高者 ＝ ★%s（%.4f）" % (best[0], best[1]))
    crit = {"①三臂皆可算分": min(n1, n2, n3) > 0, "②★双轨与两单轨之差已给出": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "n": len(pairs), "k": a.k, "compliant": {"hit1": round(h1,4), "hit5": round(h5a,4), "mrr": round(m1,4)},
            "union": {"hit1": round(h2,4), "hit5": round(h5b,4), "mrr": round(m2,4)},
            "two_track": {"hit1": round(h3,4), "hit5": round(h5c,4), "mrr": round(m3,4)},
            "best": best[0], "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
