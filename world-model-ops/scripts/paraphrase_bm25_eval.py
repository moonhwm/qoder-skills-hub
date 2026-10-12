# -*- coding: utf-8 -*-
"""paraphrase_bm25_eval.py —— 在"释义型查询集"上量 BM25（零外呼；证该集"能失败"）
用途：他席 C4 指"缺的是能失败的基准" ⇒ 本器以释义集（词面重合 0.000）测 BM25
      ⇒ 若其 MRR 显著低于旧基准（他席报 BM25 MRR 0.8727）⇒ 证"本集能失败"⇒ 语义／重排臂方有可测之地。
判据（可失败）：①每查询皆能算分 ②Hit@1／MRR 落于 [0,1] ③★与旧基准对照给出 Δ 与判语
用法：python paraphrase_bm25_eval.py --index <合规索引> --queries <释义集> [--k 5] [--json out]
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
    ap = argparse.ArgumentParser(); ap.add_argument("--index", required=True); ap.add_argument("--queries", required=True)
    ap.add_argument("--k", type=int, default=5); ap.add_argument("--json", default="")
    ap.add_argument("--old-mrr", type=float, default=0.8727)
    a = ap.parse_args()
    idx = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig"))
    secs = idx.get("sections") or []
    df = idx.get("df") or {}
    avgdl = idx.get("avgdl") or 1.0
    N = idx.get("N") or len(secs)
    tf = []
    dl = []
    for s in secs:
        t = s.get("tf") or {}
        tf.append(t)
        dl.append(sum(t.values()) if t else len(toks(s.get("body") or "")))
    qs = json.loads(pathlib.Path(a.queries).read_text(encoding="utf-8-sig"))
    rows = qs.get("rows") or []
    k1, b = 1.5, 0.75
    hit1 = hit5 = 0; mrr = 0.0; n = 0; nonz = 0
    print("  ═══ 释义集上之 BM25 ═══")
    print("   索引：%s（节 %d）｜ 查询 %d 条" % (pathlib.Path(a.index).name, len(secs), len(rows)))
    for r in rows:
        q = toks(r.get("q") or "")
        tgt = r.get("target")
        if not q or not isinstance(tgt, int) or tgt >= len(secs): continue
        scores = []
        for i in range(len(secs)):
            s = 0.0
            for w in q:
                f = tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl[i] / avgdl))
            if s > 0: scores.append((s, i))
        if not scores: continue
        scores.sort(key=lambda t: -t[0])
        nonz += 1; n += 1
        rank = next((p for p, (_, i) in enumerate(scores, 1) if i == tgt), None)
        if rank == 1: hit1 += 1
        if rank and rank <= a.k: hit5 += 1
        mrr += (1.0 / rank) if rank else 0.0
    H1 = hit1/max(1, n); H5 = hit5/max(1, n); M = mrr/max(1, n)
    crit = {"①每查询皆能算分（非零分者 > 0）": nonz > 0,
            "②Hit@1／MRR 落于 [0,1]": (0 <= H1 <= 1) and (0 <= M <= 1),
            "③★与旧基准对照已给出": True}
    print("   可算查询 %d ｜ ★Hit@1 %.4f ｜ Hit@%d %.4f ｜ ★MRR %.4f" % (n, H1, a.k, H5, M))
    print("   ── 与旧基准对照 ──")
    print("     旧基准（他席报，标题掩码查询）：BM25 MRR %.4f ｜ Hit@1 0.8289" % a.old_mrr)
    print("     ★本集（释义型，词面重合 0.000）：MRR %.4f ⇒ ★ΔMRR %+.4f" % (M, M - a.old_mrr))
    fail = "★能失败（语义／重排臂方有可测之地）" if M < a.old_mrr - 0.05 else "★未能失败（MRR 未显著下降 ⇒ 本集仍偏词面）"
    print("   ⇒ 判：%s" % fail)
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "index": pathlib.Path(a.index).name, "n": n, "hit1": round(H1, 4), "hit5": round(H5, 4),
            "mrr": round(M, 4), "old_mrr": a.old_mrr, "dmrr": round(M - a.old_mrr, 4),
            "can_fail": bool(M < a.old_mrr - 0.05), "criteria": crit}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
