# -*- coding: utf-8 -*-
"""b_doc_eval.py —— 档级释义集之评测（零外呼）：BM25 是否"能失败"
目标粒度＝"档"：命中＝top-k 中出现★目标档之任一节（doc-level 命中）
对照＝A 组（取节正文中段 12 字之字面查询，§级）
判据（可失败）：①每条查询皆解析出目标档；②两集皆可算分；③★ΔMRR（档级释义 − 字面）显著为负
用法：python b_doc_eval.py --index <合规索引> --set <档级集json> [--k 5] [--json out]
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
    tf = []; dl = []
    for s in secs:
        t = s.get("tf") or {}
        tf.append(t); dl.append(sum(t.values()) if t else len(toks(s.get("body") or "")))
    pairs = json.loads(pathlib.Path(a.set).read_text(encoding="utf-8-sig"))["pairs"]

    def rank(q):
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

    rows = []; miss = 0
    for q, key in pairs:
        tgts = [i for i, s in enumerate(secs) if key in str(s.get("doc") or "")]
        if not tgts: miss += 1; continue
        order = rank(q); pos = [p for p, i in enumerate(order, 1) if i in tgts]
        r = min(pos) if pos else None
        rows.append({"q": q, "doc": key, "rank": r, "n_tgt": len(tgts)})
    n = len(rows)
    H1 = sum(1 for r in rows if r["rank"] == 1)/max(1, n)
    H5 = sum(1 for r in rows if r["rank"] and r["rank"] <= a.k)/max(1, n)
    M = sum((1.0/r["rank"]) if r["rank"] else 0.0 for r in rows)/max(1, n)
    # A 组对照：节正文中段 12 字（字面查询，§级）
    A = []
    for i, s in enumerate(secs[:120]):
        b = re.sub(r"\s+", "", s.get("body") or "")
        if len(b) < 80: continue
        span = b[len(b)//2: len(b)//2+12]
        if len(span) < 8: continue
        order = rank(span)
        A.append(order.index(i)+1 if i in order else None)
    AM = sum((1.0/r) if r else 0.0 for r in A)/max(1, len(A))
    AH1 = sum(1 for r in A if r == 1)/max(1, len(A))
    crit = {"①每条查询皆解析出目标档（未解析 0）": miss == 0,
            "②两集皆可算分": n > 0 and len(A) > 0,
            "③★ΔMRR（档级释义 − 字面）显著为负（≤−0.05）": (M - AM) <= -0.05}
    print("  ═══ 档级释义集之 BM25 ═══")
    print("   档级释义：%d 条（未解析 %d）" % (len(pairs), miss))
    print("   ★档级释义：Hit@1 %.4f ｜ Hit@%d %.4f ｜ ★MRR %.4f" % (H1, a.k, H5, M))
    print("   字面对照（A 组，N=%d）：Hit@1 %.4f ｜ ★MRR %.4f" % (len(A), AH1, AM))
    print("   ⇒ ★ΔMRR ＝ %+.4f ⇒ %s" % (M - AM, "★能失败（语义有空间）" if (M - AM) <= -0.05 else "★未能失败"))
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ── 样例（前 6，含档级名次）──")
    for r in rows[:6]: print("      rank=%-5s ｜ %-30s ⇒ %s" % (r["rank"], r["q"][:28], r["doc"][:22]))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "n": n, "hit1": round(H1, 4), "hit5": round(H5, 4), "mrr": round(M, 4),
            "A": {"n": len(A), "hit1": round(AH1, 4), "mrr": round(AM, 4)}, "dmrr": round(M - AM, 4),
            "criteria": crit, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
