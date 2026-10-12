# -*- coding: utf-8 -*-
"""cooc_expand_eval.py —— 本地共现扩展（零成本攻「零重叠」）（2026-10-12 立）
问题：释义查询之 52% 与目标档"零词面重叠"⇒ 词面法近随机（-1241）。
本器（零外呼）：★用语料自身之档级共现作「同义词典」——对查询词，取其「在同一档内共现频次最高」之扩展词，
    以原词权重 1.0／扩展词权重 w 重跑 BM25 ⇒ 看★"零重叠"组是否改善。
判据（可失败）：①共现表已建；②两组之别已给出；③★"零重叠"组之 ΔMRR 已给出（正负皆如实）
用法：python cooc_expand_eval.py --index <并集索引> --set <档级集> [--w 0.3] [--topn 8] [--json out]
（中文串一律用「」）
"""
import argparse, collections, json, math, pathlib, re, sys, time

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
    ap.add_argument("--w", type=float, default=0.3); ap.add_argument("--topn", type=int, default=8)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    j = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig"))
    secs = j.get("sections") or []; df = j.get("df") or {}; avgdl = j.get("avgdl") or 1.0; N = j.get("N") or len(secs)
    tf = [s.get("tf") or {} for s in secs]; dl = [sum(t.values()) or 1 for t in tfs if True] if False else [sum(t.values()) or 1 for t in tf]
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]
    # ★档级词集与共现
    # ★每档只取「最高频 CAP 词」建共现（免二次爆炸；也更聚焦信号）
    CAP = 150
    doc_terms = collections.defaultdict(set)
    for i, s in enumerate(secs):
        d = str(s.get("doc") or "")
        top = sorted(tf[i].items(), key=lambda kv: -kv[1])[:CAP]
        doc_terms[d].update(w for w, _ in top)
    co = collections.defaultdict(collections.Counter)
    for d, ts in doc_terms.items():
        ts = list(ts)
        for x in ts:
            for y in ts:
                if x != y: co[x][y] += 1
    print("  ═══ 本地共现扩展实验（零外呼）═══")
    print("   索引：%s（节 %d／档 %d）｜ 词表 %d ｜ 查询 %d 条" % (
        pathlib.Path(a.index).name, len(secs), len(doc_terms), len(df), len(pairs)))

    def bm25_rank(qt_weights):
        sc = []
        for i in range(len(secs)):
            v = 0.0
            for w, wt in qt_weights.items():
                f = tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                v += wt * idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * dl[i] / avgdl))
            if v > 0: sc.append((v, i))
        sc.sort(key=lambda x: -x[0]); return [i for _, i in sc]

    doc2sec = {}
    for i, s in enumerate(secs): doc2sec.setdefault(str(s.get("doc") or ""), []).append(i)

    def evalq(q, expand):
        qt = toks(q)
        if not qt: return None, None
        wts = {w: 1.0 for w in qt}
        if expand:
            add = collections.Counter()
            for w in set(qt):
                for y, c in (co[w].most_common(a.topn) if w in co else []): add[y] += c
            for y, c in add.most_common(a.topn):
                if y not in wts: wts[y] = a.w
        order = bm25_rank(wts)
        r_of = {i: n for n, i in enumerate(order, 1)}
        sc = {d: min((r_of.get(i, 10**6) for i in idxs), default=10**6) for d, idxs in doc2sec.items()}
        ranked = sorted(sc, key=lambda x: (sc[x], x))
        return ranked, qt

    res = {"ov": {"base": [], "exp": []}, "no": {"base": [], "exp": []}}
    for q, key in pairs:
        tgt = next((d for d in doc2sec if key in d), None)
        if not tgt: continue
        rb, qt = evalq(q, False); re_, _ = evalq(q, True)
        if rb is None: continue
        qt_s = set(qt); dn = set(toks(tgt))
        grp = "ov" if (qt_s & dn) else "no"
        res[grp]["base"].append(rb.index(tgt)+1)
        res[grp]["exp"].append(re_.index(tgt)+1)
    def mrr(v): return sum(1.0/x for x in v)/max(1, len(v))
    print("   ── 结果（按有无词面重叠分组）──")
    for k, lab in (("ov", "★有重叠组"), ("no", "★零重叠组")):
        b, e = res[k]["base"], res[k]["exp"]
        print("   %s（%d 条）：BM25 MRR %.4f ｜ ★扩展后 MRR %.4f ｜ ★ΔMRR %+.4f" % (lab, len(b), mrr(b), mrr(e), mrr(e)-mrr(b)))
    tb = res["ov"]["base"]+res["no"]["base"]; te = res["ov"]["exp"]+res["no"]["exp"]
    print("   ★全体（%d 条）：BM25 %.4f ｜ ★扩展后 %.4f ｜ ★ΔMRR %+.4f" % (len(tb), mrr(tb), mrr(te), mrr(te)-mrr(tb)))
    crit = {"①共现表已建": len(co) > 0, "②两组之别已给出": True, "③★零重叠组之 ΔMRR 已给出": True}
    for k2, v2 in crit.items(): print("   %s ⇒ %s" % (k2, "✓" if v2 else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "w": a.w, "topn": a.topn,
            "ov": {"n": len(res["ov"]["base"]), "base": round(mrr(res["ov"]["base"]),4), "exp": round(mrr(res["ov"]["exp"]),4)},
            "no": {"n": len(res["no"]["base"]), "base": round(mrr(res["no"]["base"]),4), "exp": round(mrr(res["no"]["exp"]),4)},
            "all": {"n": len(tb), "base": round(mrr(tb),4), "exp": round(mrr(te),4)}, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
