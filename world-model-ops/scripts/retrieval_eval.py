# -*- coding: utf-8 -*-
"""retrieval_eval.py —— 检索评测（乙案：scope ＋ 三路重排对拍 ＋ P@1／P@5／MRR 对 BM25 基线）
承他席 P1–P6：「评测判据（能失败）：P@1 / P@5 / MRR 对 BM25 基线；消融组（仅 BM25／仅向量／向量+重排）三组对照，若融合不优于 BM25 基线须如实报负结果」
★金标两组（★先定后跑，避免泄漏）：
  A「已知项」组：★确定性抽样（每 260 节取 1）取其正文中段 12 字为查询 ⇒ 金标＝该节（doc,i）
     ★须声明：此组为"逐字命中"型，★系统性偏向词法（BM25）—— 故 B 组不可省
  B「释义」组：★手写 6 条释义式查询（不含原句），金标＝目标节之标题子串（目标由我事先认定）
★模式：bm25（基线）｜rrf（BM25 与 二元组 TF-IDF 余弦 之倒数秩融合）｜mmr（在融合候选上做最大边际相关）
★scope：all／outline（纲要）／artifact（件）
用法：python retrieval_eval.py [--scope all] [--top 5] [--json out]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, re, sys
from collections import Counter

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"   # ★件号映射与索引源
import os as _os
IDX = pathlib.Path(_os.environ["OPL_SECTION_IDX"]) if _os.environ.get("OPL_SECTION_IDX") else (SEAT/"exp"/".cache"/"section_index.json")

def toks(s, n=2):
    s = re.sub(r"\s+", "", s)
    out = [s[i:i+n] for i in range(len(s)-n+1)]
    out += re.findall(r"[A-Za-z0-9_\-]{2,}", s)
    return out

def art_map():
    """★件号 ↔ doc 标题 映射（2026-10-12）：索引之 doc ＝ 文件名 split("_")[0]（中文标题），★不含件号
    ⇒ 扫交换区文件名（<标题>_DF-…-CAIRN-<nn>.otl）建映射，供"件号直通车"用；不动索引、零花费"""
    m = {}
    for f in EX.glob("*.otl"):
        mm = re.search(r"CAIRN-(\d{1,3})", f.name)
        if mm: m["CAIRN-%s" % mm.group(1)] = f.name.split("_")[0]
    return m


def load():
    if not IDX.exists():
        print("  ★索引不在（先跑 section_search.py --build）⇒ 未测（退出码 2）"); sys.exit(2)
    d = json.loads(IDX.read_text(encoding="utf-8"))
    # ★自纠（2026-10-12）：既有索引★不含 tf ⇒ 直接打分会对全部节打 0 分、排序退化为原序
    #   ⇒ 此处就地补齐 tf 并由之自洽重算 df／N／avgdl（★只读原索引、不写盘）
    if not any("tf" in s for s in d["sections"]):
        df = Counter()
        for s in d["sections"]:
            s["tf"] = dict(Counter(toks(s.get("body", "") + " " + s.get("head", ""))))
            for w in s["tf"]: df[w] += 1
        d["df"] = dict(df)
        d["N"] = len(d["sections"])
        d["avgdl"] = sum(sum(s["tf"].values()) for s in d["sections"]) / max(1, d["N"])
        print("   ★自纠：原索引无 tf ⇒ 已就地补齐（%d 节；df %d 词；avgdl %.1f）" % (d["N"], len(df), d["avgdl"]))
    return d

def bm25_scores(d, q, allow=None):
    N, avg, df = d["N"], d["avgdl"], d["df"]
    k1, b = 1.5, 0.75
    qtf = Counter(toks(q))
    out = []
    for s in d["sections"]:
        tf, dl = s.get("tf") or {}, sum((s.get("tf") or {}).values()) or 1
        sc = 0.0
        for w, qn in qtf.items():
            f = tf.get(w, 0)
            if not f: continue
            n = df.get(w, 0)
            idf = math.log(1 + (N - n + 0.5)/(n + 0.5))
            sc += idn(idf, f, dl, avg, k1, b) * qn
        out.append(sc if (allow is None or len(out) in allow) else -1e9)
    return out

def idn(idf, f, dl, avg, k1, b):
    return idf * (f*(k1+1)) / (f + k1*(1 - b + b*dl/avg))

def cos_scores(d, q, allow=None):
    N, df = d["N"], d["df"]
    qtf = Counter(toks(q))
    qv = {w: (1+math.log(c)) * math.log(1 + N/(1+df.get(w, 0))) for w, c in qtf.items()}
    qn = math.sqrt(sum(v*v for v in qv.values())) or 1.0
    out = []
    for s in d["sections"]:
        tf = s.get("tf") or {}
        dl = sum(tf.values()) or 1
        num = 0.0; den = 0.0
        for w, c in tf.items():
            wgt = (1+math.log(c)) * math.log(1 + N/(1+df.get(w, 0)))
            den += wgt*wgt
            if w in qv: num += wgt*qv[w]
        sc2 = num/((math.sqrt(den) or 1.0)*qn)
        out.append(sc2 if (allow is None or len(out) in allow) else -1e9)
    return out

def ranks(scores):
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    r = {}
    for pos, i in enumerate(order, 1): r[i] = pos
    return order, r

def rrf(d, q, k=60, allow=None):
    s1 = bm25_scores(d, q, allow); s2 = cos_scores(d, q, allow)
    o1, r1 = ranks(s1); o2, r2 = ranks(s2)
    fused = {i: 1/(k + r1[i]) + 1/(k + r2[i]) for i in range(len(s1))}
    return sorted(fused, key=lambda i: -fused[i]), fused

def mmr(d, q, lam=0.7, topn=50, allow=None):
    order, fused = rrf(d, q, allow=allow)
    cand = order[:topn]
    pos_of = {i: j for j, i in enumerate(cand)}          # ★自纠：节索引 → 位置（原先以节索引直接索引位置表 ⇒ 越界）
    tokset = [set(toks(d["sections"][i].get("body", "")[:400])) for i in cand]
    sel = []
    while cand:
        best, bi = None, None
        for j, i in enumerate(cand):
            rel = fused[i]
            div = max([len(tokset[j] & tokset[pos_of[k]])/max(1, len(tokset[j] | tokset[pos_of[k]]))
                       for k in sel if k in pos_of], default=0.0)
            v = lam*rel - (1-lam)*div
            if best is None or v > best: best, bi = v, j
        sel.append(cand.pop(bi))
    rest = [i for i in order if i not in sel]
    return sel + rest

def measure(d, order, gold, ks=(1, 5)):
    res = {}
    for k in ks:
        hit = sum(1 for g in gold if gold.index(g) < k and g in order[:k])
        res["P@%d" % k] = round(hit/len(gold), 3) if gold else 0.0
    rr = []
    for g in gold:
        rr.append(1.0/(order.index(g)+1) if g in order else 0.0)
    res["MRR"] = round(sum(rr)/len(rr), 3) if rr else 0.0
    return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scope", default="all"); ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--router", default="none", choices=["none", "score", "oracle", "kw", "multi", "multi2"])   # ★两段式：先选域、后检索
    ap.add_argument("--json", default="")
    ap.add_argument("--query", default="")          # ★分型使用：可直接当检索器用
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--assert-baseline", action="store_true")   # ★回归判据：与 -1131/-1130 之六设置读数比对，漂移即红
    a = ap.parse_args()
    d = load()
    secs = d["sections"]
    scope_idx = [i for i, s in enumerate(secs)
                 if a.scope == "all" or (a.scope == "outline" and "纲要" in s["doc"]) or (a.scope == "artifact" and "纲要" not in s["doc"])]
    print("  ═══ 检索评测（乙案）｜ 节 %d ｜ scope=%s ⇒ %d 节 ═══" % (len(secs), a.scope, len(scope_idx)))
    # A 组：确定性抽样（每 260 节取 1）之正文中段 12 字为查询
    A = []
    for n, i in enumerate(range(0, len(secs), 260)):
        b = re.sub(r"\s+", "", secs[i].get("body", ""))
        if len(b) < 80: continue
        span = b[len(b)//2: len(b)//2 + 12]
        if len(span) < 8: continue
        A.append({"q": span, "gold_i": i, "gold_head": secs[i]["head"][:40], "kind": "已知项"})
    # B 组：手写释义（不含原句）＋ 目标节标题子串（事先认定）
    B_SPEC = [
        ("动手之前该先核什么，此项义务之章次", "总线先行"),
        ("新技能要怎样登记才算合规", "技能录入"),
        ("谁能替我干活、异种模型可否并用", "子代理"),
        ("消息重复投递与异常补偿之机制", "事件驱动架构"),
        ("研究要做到什么程度才合要求", "穷举研究"),
        ("插件框架之名与用处", "Cordis"),
        ("开源社区如何治理", "治理架构"),
        ("跨平台数据怎样达成一致", "共识机制"),
        ("对本文件自身作出永久性修正", "自指订正"),
        ("仓内目录应当怎么摆", "目录结构"),
        ("商业与人的发展之关系", "自由全面发展"),
        ("底层协同与全栈实现", "全栈开发"),
    ]
    B = []
    KW_OUTLINE = ("纲要", "章", "要求", "准则", "规范", "共识", "治理", "声明", "序言", "义务", "机制", "架构")
    for q, key in B_SPEC:
        tgt = [i for i, s in enumerate(secs) if key in (s["head"] or "")]
        B.append({"q": q, "gold_i": tgt[0] if tgt else None, "gold_key": key, "kind": "释义"})
    allow_set = set(scope_idx)
    # ★两段式检索之域集合与路由（2026-10-12）
    OUTLINE_IDX = [i for i, s in enumerate(secs) if "纲要" in s["doc"]]
    ART_IDX = [i for i, s in enumerate(secs) if "纲要" not in s["doc"]]
    DOMAINS = {"outline": set(OUTLINE_IDX), "artifact": set(ART_IDX)}

    def route(q, gold_i=None):
        """返回本查询应限定之域索引集合：score＝按各域 top-1 BM25 分择优（无金标泄漏）；oracle＝用金标所在域（上界参照）"""
        if a.router == "oracle" and gold_i is not None:
            return DOMAINS["outline"] if gold_i in DOMAINS["outline"] else DOMAINS["artifact"]
        if a.router == "kw":
            return DOMAINS["outline"] if any(w in q for w in KW_OUTLINE) else DOMAINS["artifact"]
        best, bd = None, None
        for name, allow in DOMAINS.items():
            sc = bm25_scores(d, q, allow)
            top = max(sc) if sc else -1e9
            if best is None or top > best: best, bd = top, name
        return DOMAINS[bd]
    print("   金标：A 已知项 %d 条｜B 释义 %d 条（★B 中有 %d 条未在库中命中标题，剔除）" % (
        len(A), len(B), sum(1 for x in B if x["gold_i"] is None)))
    import hashlib as _hl
    out = {"scope": a.scope, "n_sections": len(secs), "index_sha16": _hl.sha3_256(IDX.read_bytes()).hexdigest()[:16], "modes": {}}
    for mode in ("bm25", "rrf", "mmr"):
        per = {}
        # ★按域筛金标（2026-10-12 自纠）：域外金标不可达 ⇒ 若计入即得"假红 0.000"
        for grp, items in (("A已知项", A), ("B释义", [x for x in B if x["gold_i"] is not None])):
            if a.scope != "all":
                items = [x for x in items if x["gold_i"] in allow_set]
                if not items:
                    out.setdefault("modes", {}).setdefault(mode, {})[grp] = {"P@1": None, "P@5": None, "MRR": None, "n": 0, "note": "★域内无金标 ⇒ 不可评（非 0）"}
                    print("   %-5s ｜ %s：★域内无金标 ⇒ 不可评（非 0）" % (mode, grp)); continue
            gold = [x["gold_i"] for x in items]
            agg = {"P@1": [], "P@5": [], "MRR": []}
            routed = 0
            for x in items:
                if a.router in ("multi", "multi2"):
                    # ★多域并行融合（2026-10-12）：各域各取 top-k，按域内秩融合 ⇒ ★不需路由准确率
                    #   multi ＝原始秩 RRF（★小域被系统性抬升）；multi2 ＝域内秩归一（r/len(dom)）后再融合
                    fused = {}
                    for _nm, _dom in DOMAINS.items():
                        _sc = bm25_scores(d, x["q"], _dom)
                        _, _r = ranks(_sc)
                        for _i in _dom:
                            _rn = (_r[_i]/max(1, len(_dom))) if a.router == "multi2" else _r[_i]
                            fused[_i] = fused.get(_i, 0.0) + 1.0/(60 + _rn*60 if a.router == "multi2" else 60 + _rn)
                    order = sorted(fused, key=lambda i: -fused[i]) + [i for i in range(len(secs)) if i not in fused]
                    m = measure(d, order, [x["gold_i"]])
                    for k in agg: agg[k].append(m[k])
                    routed += 1
                    continue
                mask = allow_set if a.router == "none" else route(x["q"], x["gold_i"])
                if x["gold_i"] not in mask:
                    # ★自纠四（2026-10-12）：路由错域者★计为未命中（贡献 0），★不得剔除
                    #   —— 剔除只留「路由对」之样本 ⇒ 幸存者偏差 ⇒ 指标虚高（假绿）
                    for k in agg: agg[k].append(0.0)
                    continue
                routed += 1
                if mode == "bm25": order, _ = ranks(bm25_scores(d, x["q"], mask))
                elif mode == "rrf": order, _ = rrf(d, x["q"], allow=mask)
                else: order = mmr(d, x["q"], allow=mask)
                m = measure(d, order, [x["gold_i"]])
                for k in agg: agg[k].append(m[k])
            if not agg["MRR"]:
                out.setdefault("modes", {}).setdefault(mode, {})[grp] = {"P@1": None, "P@5": None, "MRR": None, "n": 0, "note": "★路由后域内无金标 ⇒ 不可评"}
                print("   %-5s ｜ %s：★路由后域内无金标 ⇒ 不可评" % (mode, grp)); continue
            per[grp] = {k: round(sum(v)/max(1, len(v)), 3) for k, v in agg.items()}
            per[grp]["n"] = routed
        out["modes"][mode] = per
        print("   %-5s ｜ A 已知项 P@1 %.3f P@5 %.3f MRR %.3f（n=%d）｜ B 释义 P@1 %.3f P@5 %.3f MRR %.3f（n=%d）" % (
            mode, per["A已知项"]["P@1"], per["A已知项"]["P@5"], per["A已知项"]["MRR"], per["A已知项"]["n"],
            per["B释义"]["P@1"], per["B释义"]["P@5"], per["B释义"]["MRR"], per["B释义"]["n"]))
    bm = out["modes"]["bm25"]
    verdict = []
    for mode in ("rrf", "mmr"):
        for grp in ("A已知项", "B释义"):
            if out["modes"][mode][grp]["MRR"] > bm[grp]["MRR"]: verdict.append("%s 优于 bm25（%s）" % (mode, grp))
            elif out["modes"][mode][grp]["MRR"] < bm[grp]["MRR"]: verdict.append("★%s 劣于 bm25（%s）" % (mode, grp))
            else: verdict.append("%s 与 bm25 持平（%s）" % (mode, grp))
    print("   ⇒ 判：%s" % "；".join(verdict))
    # ★分型使用（2026-10-12）：释义／规范类 ⇒ multi（各域平等发言）；其余 ⇒ none（全域平检索）
    if a.query:
        KW_SPEC = ("纲要", "规范", "要求", "机制", "义务", "准则", "共识", "治理", "章程", "架构", "声明")
        strat = "multi" if any(w in a.query for w in KW_SPEC) else "none"
        print("   ★分型：查询「%s」⇒ 策略=%s" % (a.query[:26], strat))
        # ★件号直通车（2026-10-12）：查询含 CAIRN-<nn> ⇒ 先经 art_map 定位该件之 doc 标题，再在该子集内检索
        AM = art_map()
        _m = re.search(r"CAIRN-(\d{1,3})", a.query, re.I)
        _direct = None
        if _m:
            _key = "CAIRN-%s" % _m.group(1)
            _title = AM.get(_key)
            if _title:
                _sub = [i for i, s in enumerate(secs) if s["doc"] == _title]
                if _sub:
                    _direct = set(_sub)
                    print("   ★件号直通车：%s ⇒ doc「%s」（%d 节）｜映射表 %d 条" % (_key, _title[:26], len(_sub), len(AM)))
        if _direct:
            _sc = bm25_scores(d, a.query, _direct)
            order = [i for i, v in sorted(enumerate(_sc), key=lambda t: -t[1]) if i in _direct]
        else:
            fused = {}
            for _nm, _dom in DOMAINS.items():
                sc = bm25_scores(d, a.query, _dom)
                _, r = ranks(sc)
                for i in _dom:
                    fused[i] = fused.get(i, 0.0) + (1.0/(60 + r[i]) if strat == "multi" else 0.0)
            if strat == "none":
                order, _ = ranks(bm25_scores(d, a.query, None))
            else:
                order = sorted(fused, key=lambda i: -fused[i]) + [i for i in range(len(secs)) if i not in fused]
        print("   命中前 %d：" % a.k)
        for pos, i in enumerate(order[:a.k], 1):
            s = secs[i]
            print("     %d. [%s] %s ｜ %s" % (pos, s["doc"][:18], (s["head"] or "")[:34], (s["body"] or "")[:44].replace("\n", " ")))
    # ★回归判据（可失败）：以 -1130／-1131 之六设置为基线，漂移超容差即红
    if a.assert_baseline:
        # ★基线须绑"索引指纹"（2026-10-12）：语料一变，读数即变 ⇒ 不同档之基线不可互比
        BASE_IDX = "2c4a8f9a1e7b3d55"   # 旧档（3,126 节）指纹（★重建后须重录）
        if out.get("index_sha16") != BASE_IDX:
            print("   ★索引指纹不同（记 %s，今 %s）⇒ ★旧基线不适用：仅列本轮新读数，不判红" % (BASE_IDX, out.get("index_sha16")))
        BASE = {("none", "B释义"): 0.687, ("multi", "B释义"): 0.944, ("oracle", "B释义"): 0.958,
                ("multi2", "B释义"): 0.015, ("none", "A已知项"): 0.801, ("multi", "A已知项"): 0.407}
        bad = []; checked = 0
        # ★自纠六（2026-10-12）：平表含其它 router 之期望 ⇒ 单跑一路时必然"不匹配"而报红
        #   ⇒ ★只断言"本次所跑 router"之项（全量回归须逐 router 逐一跑）
        for (rt, grp), want in BASE.items():
            if rt != a.router: continue
            if out.get("index_sha16") != BASE_IDX: continue
            checked += 1
            got = out.get("modes", {}).get("bm25", {}).get(grp, {}).get("MRR")
            if got is None: bad.append("%s/%s 未测" % (rt, grp)); continue
            if abs(got - want) > 0.02: bad.append("%s/%s 期望 %.3f 实得 %.3f" % (rt, grp, want, got))
        print("   ★回归判据（本轮 router=%s）：应查 %d 项 ⇒ %s" % (a.router, checked, "✓ 无漂移" if not bad else "✗ " + "；".join(bad[:4])))
        if bad: print("   ⇒ ★构建红（检索行为已漂移）")
    out["verdict"] = verdict
    if a.json: pathlib.Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("   ★声明一：分域读数已按域筛金标（域外金标剔除，免「假红 0.000」；域内无金标则报「不可评」而非 0）")
    print("   ★声明二（金标之偏向）：A 组为「逐字命中」型 ⇒ ★系统性偏向词法；故结论须并读 B 组")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
