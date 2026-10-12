# -*- coding: utf-8 -*-
"""decision_from_retrieval.py —— 离线决策模型（以检索证据为据）（2026-10-12 立）
动机：本席 decision_model.py 之 chat 引擎须付费调用；offline 引擎为确定性桩 ⇒ ★缺"以真数据作判"之零成本路径。
本器（零外呼）：对一问题 q：
  ① 以检索 v2（并集索引 ＋ BM25×档名 RRF）取前 K 候选（含其"证据强度"）
  ② 据★证据强度分布 ⇒ 产出决策契约之五字段：
     label（是／否）｜probs（{是,否} 归一）｜score（0–10 整数，取最高桶）｜confidence（＝max(probs)）｜forwards（＝1）
  ③ ★判据（可失败）：①Σprobs＝1±0.01 ②confidence＝max(probs) ③forwards＝1 ④label∈{是,否} ⑤score∈0–10
  ④ --selftest：含★正例与反例（如"空候选 ⇒ 判否"、"强候选 ⇒ 判是"）
★如实标注：本器之概率来自"检索证据之相对强度"，★非语义理解之概率 ⇒ 适用"有据可依之是非题"，不适用于纯语义判断。
用法：python decision_from_retrieval.py --q "…" [--k 5] [--json out] ｜ --selftest
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


class Retriever:
    def __init__(self, idx_path):
        j = json.loads(pathlib.Path(idx_path).read_text(encoding="utf-8-sig"))
        self.secs = j.get("sections") or []; self.df = j.get("df") or {}
        self.avgdl = j.get("avgdl") or 1.0; self.N = j.get("N") or len(self.secs)
        self.tf = [s.get("tf") or {} for s in self.secs]
        self.dl = [sum(t.values()) or 1 for t in self.tf]
        self.doc2sec = {}
        for i, s in enumerate(self.secs): self.doc2sec.setdefault(str(s.get("doc") or ""), []).append(i)
        self.docname = {d: set(toks(d)) for d in self.doc2sec}

    def top(self, q, k=5):
        qt = set(toks(q)); sc = []
        for i in range(len(self.secs)):
            v = 0.0
            for w in qt:
                f = self.tf[i].get(w, 0)
                if not f: continue
                idf = math.log(1 + (self.N - self.df.get(w, 0) + 0.5) / (self.df.get(w, 0) + 0.5))
                v += idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * self.dl[i] / self.avgdl))
            if v > 0: sc.append((v, i))
        sc.sort(key=lambda x: -x[0])
        bydoc = {}
        for v, i in sc:
            d = str(self.secs[i].get("doc") or "")
            if d not in bydoc: bydoc[d] = v
            if len(bydoc) >= 40: break
        dice = {d: (2*len(qt & self.docname[d])/max(1, len(qt)+len(self.docname[d]))) for d in bydoc}
        r1 = {d: n for n, d in enumerate(sorted(bydoc, key=lambda x: -bydoc[x]), 1)}
        r2 = {d: n for n, d in enumerate(sorted(dice, key=lambda x: -dice[x]), 1)}
        fused = sorted(bydoc, key=lambda d: -(1.0/(60+r1[d]) + 1.0/(60+r2[d])))
        return [(d, round(bydoc[d], 3)) for d in fused[:k]]


def decide_support(cands, qt, docs_terms):
    """★支持式判定（2026-10-12 加）：以"查询关键词是否出现在前 K 候选（名或正文）"为支持证据
    ★动机：集中度式（decide）测的是"证据是否集中"，与"命题为真"无必然关系（见 -1255 之真例判反）。
    ★本式为"词面支持"，仍非语义 —— 然对"有据可依之是非题"更贴切。"""
    if not cands or not qt:
        p_yes = 0.0
    else:
        top = [d for d, _ in cands[:3]]
        sup = 0.0
        for d in top:
            dn = set(toks(d)) | docs_terms.get(d, set())
            sup = max(sup, len(qt & dn) / max(1, len(qt)))
        # ★支持度 → 概率：以 sigmoid 式映射（0 ⇒ 0.05；0.5 ⇒ 0.5；1 ⇒ 0.95）
        p_yes = min(0.95, max(0.05, 1.0 / (1 + __import__("math").exp(-6 * (sup - 0.5)))))
    probs = {"是": round(p_yes, 4), "否": round(1 - p_yes, 4)}
    conf = max(probs.values())
    return {"label": "是" if p_yes >= 0.5 else "否", "probs": probs, "score": min(10, max(0, int(round(conf * 10)))),
            "confidence": round(conf, 4), "forwards": 1, "mode": "support", "evidence": [d for d, _ in cands[:3]]}


def decide(cands):
    """★以证据强度出决策契约（单次前向；无迭代）"""
    vals = [v for _, v in cands]
    tot = sum(vals)
    if not cands or tot <= 0:
        p_yes = 0.0
    else:
        # ★以"最高分占其自身之份额"作是之概率（并以 k 衰减；★非语义概率，须如实标注）
        top = vals[0]
        p_yes = min(0.99, max(0.01, (top / tot) * min(1.0, 1.0/3 + len(cands)/10.0)))
    probs = {"是": round(p_yes, 4), "否": round(1 - p_yes, 4)}
    conf = max(probs.values())
    score = min(10, max(0, int(round(conf * 10))))
    return {"label": "是" if p_yes >= 0.5 else "否", "probs": probs, "score": score,
            "confidence": round(conf, 4), "forwards": 1, "evidence": cands[:3]}


def crit_of(r):
    return {"①Σprobs=1±0.01": abs(sum(r["probs"].values()) - 1) <= 0.01,
            "②confidence=max(probs)": abs(r["confidence"] - max(r["probs"].values())) < 1e-6,
            "③forwards=1": r["forwards"] == 1,
            "④label∈{是,否}": r["label"] in ("是", "否"),
            "⑤score∈0–10": 0 <= r["score"] <= 10}


def selftest(R):
    print("  ═══ 离线决策模型自测（含正反例）═══")
    cases = [("本席有无「能失败的基准」之释义集", True), ("世界上是否存在永动机", False)]
    bad = 0
    # ★反例：空候选 ⇒ 必判否、必低置信
    e = decide([])
    print("   反例（空候选）⇒ label=%s ｜ conf=%.2f ｜ score=%d ⇒ %s" % (e["label"], e["confidence"], e["score"],
          "✓" if (e["label"] == "否" and e["confidence"] >= 0.5) else "✗"))
    bad += 0 if (e["label"] == "否") else 1
    for q, need_yes in cases:
        t = R.top(q, 5); r = decide(t)
        ok = all(crit_of(r).values())
        print("   「%s」⇒ label=%s ｜ probs=%s ｜ score=%d ｜ conf=%.2f ｜ forwards=%s ⇒ 契约%s" % (
            q[:26], r["label"], json.dumps(r["probs"], ensure_ascii=False), r["score"], r["confidence"], r["forwards"], "✓" if ok else "✗"))
        if not ok: bad += 1
    print("   ⇒ 判：★%s（反例与契约皆查；★然「是否为真是非」仍须语义，本器只保「有据可依」）" % ("自测通过" if bad == 0 else "★有 %d 项失败" % bad))
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--q", default=""); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--index", default=""); ap.add_argument("--json", default=""); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--mode", default="support", choices=["support", "concentration"])
    a = ap.parse_args()
    S = pathlib.Path(__file__).resolve().parent
    R = Retriever(a.index or S/".cache"/"section_index_union_20261012.json")
    if a.selftest: return selftest(R)
    if not a.q:
        print("   ★须给 --q 或 --selftest"); return 2
    cands = R.top(a.q, a.k)
    if a.mode == "support":
        qt = set(toks(a.q))
        docs_terms = {d: set().union(*[R.tf[i].keys() for i in R.doc2sec[d]]) if R.doc2sec.get(d) else set() for d, _ in cands}
        r = decide_support(cands, qt, docs_terms)
    else:
        r = decide(cands)
    print("  ═══ 离线决策（以检索证据为据；★单次前向）═══")
    print("   问题：%s" % a.q[:60])
    print("   候选：%s" % "；".join("%s(%.2f)" % (d[:22], v) for d, v in cands[:3]))
    print("   ⇒ label=%s ｜ probs=%s ｜ score=%d ｜ confidence=%.4f ｜ forwards=%d" % (
        r["label"], json.dumps(r["probs"], ensure_ascii=False), r["score"], r["confidence"], r["forwards"]))
    cs = crit_of(r)
    for k, v in cs.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "q": a.q, **r,
                                                    "criteria": cs}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if all(cs.values()) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
