# -*- coding: utf-8 -*-
"""paraphrase_queries.py —— 构造"释义型查询集"（能失败的基准；纯本地、零花费）
由来：他席 DF-DEC-20261012-QODER-882FEC9C 之 C3/C4 指出 —— 现行基准之查询由"目标节自身标题"掩码而来
     ⇒ 词面重合近乎 oracle ⇒ BM25 近最优（Hit@1 0.8289／MRR 0.8727／recall@50 0.9737）
     ⇒ ★"本基准偏向 BM25，不能用它检验语义检索"；缺的是★能失败的基准，不是模型。
本器（★零外呼）：对每一节，从其★正文中取片段作查询，并★剔除标题中之所有词（含 2-gram 约束）
     ⇒ 得"词面重合低"之查询 ⇒ 目标节仍为该节（故有金标、可算 MRR）。
判据（可失败）：①集大小 ≥ 100；②★平均标题词覆盖率 ≤ 0.30（低重合）；③每查询皆有其目标节与节号。
用法：python paraphrase_queries.py --index <合规索引> [--n 200] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, random, re, sys, time

STOP = set("的 了 与 及 和 是 在 有 为 以 对 之 其 者 等 一 二 三 四 五 六 七 八 九 十 我 他 她 它 你 这 那 不 无 也 就 而 且 或 由 于 从 到 将 被 把 使 让 若 则 因 故 但 并 已 未 可 能 会 应 须 需 要 该 此 本 该件 本件".split())


def toks(t):
    """★轻量分词：中文按 2-gram ＋ 连写字母数字串"""
    t = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(t))
    out = []
    for w in t.split():
        if re.search(r"[\u4e00-\u9fff]", w):
            if len(w) == 1: out.append(w)
            else: out += [w[i:i+2] for i in range(len(w)-1)]
        else:
            out.append(w.lower())
    return [x for x in out if x and x not in STOP]


def split_sents(body, lo=18, hi=90):
    """★切句并留中等长度句（作查询候选）"""
    parts = re.split(r"[。；！？\n]|(?<=[a-z0-9\)])[\.;]", str(body))
    return [p.strip() for p in parts if lo <= len(p.strip()) <= hi]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--index", required=True)
    ap.add_argument("--n", type=int, default=200); ap.add_argument("--json", default="")
    ap.add_argument("--cap", type=float, default=0.0)
    a = ap.parse_args()
    j = json.loads(pathlib.Path(a.index).read_text(encoding="utf-8-sig"))
    secs = j.get("sections") or []
    rnd = random.Random(20261012)
    print("  ═══ 释义型查询集 构造 ｜ 节 %d ═══" % len(secs))
    rows = []; caps = []
    cand = list(range(len(secs)))
    rnd.shuffle(cand)
    for i in cand:
        s = secs[i]
        body = str(s.get("body") or s.get("text") or "")
        head = str(s.get("head") or s.get("title") or "")
        if len(body) < 80 or not head: continue
        ht = set(toks(head))
        if not ht: continue
        sents = split_sents(body)
        if not sents: continue
        # ★择"与标题词重合最少"之句，并列其覆盖率
        best = None
        for st in sents[:12]:
            qt = toks(st)
            if not qt: continue
            cap = len(ht & set(qt)) / max(1, len(ht))
            if best is None or cap < best[1]: best = (st, cap)
        if not best: continue
        # ★若仍不够低，则从查询中删去与标题共有之词（硬性降重合）
        qtxt = best[0]
        for w in list(ht):
            if w in qtxt: qtxt = qtxt.replace(w, "□")
        qtxt = re.sub(r"□+", "", qtxt).strip()
        qt = set(toks(qtxt))
        cap2 = len(ht & qt) / max(1, len(ht))
        if len(qtxt) < 14: continue
        rows.append({"q": qtxt, "target": i, "doc": s.get("doc"), "head": head[:60],
                     "cap_before": round(best[1], 3), "cap_after": round(cap2, 3)})
        caps.append(cap2)
        if len(rows) >= a.n: break
    n = len(rows)
    avg = sum(caps)/max(1, n)
    zero = sum(1 for c in caps if c == 0.0)
    crit = {"①集大小 ≥ 100": n >= 100,
            "②★平均标题词覆盖率 ≤ 0.30": avg <= 0.30,
            "③每查询皆有其目标节号": all(isinstance(r["target"], int) for r in rows)}
    print("   构造 %d 条 ｜ ★平均标题词覆盖率 %.3f ｜ ★零重合者 %d（%.1f%%）" % (n, avg, zero, 100.0*zero/max(1, n)))
    print("   ── 样例（前 4 条）──")
    for r in rows[:4]:
        print("      q=%s…" % r["q"][:52])
        print("        目标 节%-5d ｜ 档 %s ｜ 覆盖率 %.2f⇒%.2f" % (r["target"], str(r["doc"])[:34], r["cap_before"], r["cap_after"]))
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 判：%s" % ("✓ 已成'低词面重合'之查询集（★可作'能失败'之语义检索基准）" if all(crit.values()) else "★未达（须调参或换源）"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "src_index": pathlib.Path(a.index).name, "n": n, "avg_cap": round(avg, 4), "zero_cap": zero,
            "criteria": crit, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
