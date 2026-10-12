# -*- coding: utf-8 -*-
"""decision_llm_suite.py —— 以真分类模型测"决策上限"（2026-10-12 立，承 -1263 之判）
动机：-1263 证"语义阈值不可判真假"（0.50）；词面 support 仅 0.70（-1256）⇒ ★须以真模型测上限。
本器（付费；★闸内）：对决策基准 10 题，逐题以 ★单次前向 请模型出：
  {"label":"是|否","p_yes":0-1,"score":0-10} ⇒ 校验契约五项 ⇒ 计准确率与用量。
★安全：--dry-run 默认；真跑须 --run --budget-max（★器内闸；宁停不超）；★不回显凭据。
判据（可失败）：①计划之题数与成本上界已给；②真跑时每题皆合契约；③★准确率与词面 0.70 之对照已给出
用法：python decision_llm_suite.py ｜ --run --budget-max 0.01 [--model gpt-4o-mini]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP = "https://api.302ai.cn/v1/chat/completions"; PROXY = "http://127.0.0.1:10081"
PRICE_IN, PRICE_OUT = 0.0011, 0.0044   # 元／1k tokens（上界估）


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def evidence_for(q, R, SV, VC):
    """★取"检索证据"：语义 top-3 ＋ 词面（档名 Dice）top-3 之并，附摘要（该档首节高频词前 20）"""
    import hashlib, math
    def cos(a_, b_):
        s_ = sum(x*y for x, y in zip(a_, b_)); na_ = math.sqrt(sum(x*x for x in a_)); nb_ = math.sqrt(sum(y*y for y in b_))
        return s_/((na_*nb_) or 1e-9)
    out = []
    qv = VC.get("sha1:" + hashlib.sha1(str(q).encode("utf-8")).hexdigest()[:20])
    if qv and SV:
        for d, sc in sorted(((d, cos(qv, v)) for d, v in SV.items()), key=lambda x: -x[1])[:3]:
            out.append((d, sc))
    for d, sc in R.top(q, 3):
        if all(d != x for x, _ in out): out.append((d, None))
    txts = []
    for d, sc in out[:4]:
        idxs = R.doc2sec.get(d, [])[:1]
        summ = ""
        if idxs:
            i = idxs[0]
            summ = "、".join(list(R.tf[i].keys())[:20])
        txts.append("文档《%s》摘要：%s" % (d, summ[:200]))
    return txts


def ask(q, k, model, evidence=None):
    import urllib.request
    sys_p = ("你是本席（A2A新席_石敢当Cairn）之决策模型。★只做一次前向判断，不要推理过程。"
             "对本席语料相关之是非命题，输出严格 JSON：{\"label\":\"是\"或\"否\",\"p_yes\":0到1之小数,\"score\":0到10之整数}。"
             "★不确定时 p_yes 应接近 0.5。")
    user = q if not evidence else ("【检索到的本席语料片段】\n" + "\n".join(evidence) +
                                  "\n\n【命题】" + q + "\n★请仅据上述片段判断该命题真假；若片段未提及，p_yes 应接近 0.5。")
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 60,
                       "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": user}]},
                      ensure_ascii=False).encode()
    r = urllib.request.Request(EP, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(r, timeout=120) as resp:
        j = json.loads(resp.read().decode("utf-8", "replace"))
    txt = ((j.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    return txt, j.get("usage") or {}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget-max", type=float, default=0.0); ap.add_argument("--json", default="")
    ap.add_argument("--model", default="gpt-4o-mini"); ap.add_argument("--evidence", action="store_true"); a = ap.parse_args()
    suite = json.loads((SEAT.parent/"outbox"/"mem"/"decision_suite_20261012.json").read_text(encoding="utf-8-sig"))["items"]
    est_in = len(suite) * 200; est_out = len(suite) * 30
    cost = est_in/1000*PRICE_IN + est_out/1000*PRICE_OUT
    print("  ═══ 真分类模型测「决策上限」（★单次前向；题 %d）═══" % len(suite))
    print("   模型 %s ｜ ★计划：%d 次调用 ｜ ★成本上界 %.6f 元（估 in %d／out %d tokens）" % (a.model, len(suite), cost, est_in, est_out))
    if not a.run:
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）—— 真跑须 --run --budget-max <元>")
        return 0
    if a.budget_max <= 0 or cost > a.budget_max:
        print("   ★须 --budget-max ≥ %.6f ⇒ 拒绝执行（宁停不超）" % cost); return 2
    k = key()
    if not k: print("   ★无凭据 ⇒ 未测"); return 2
    R = None; SV = {}; VC = {}
    if a.evidence:
        import importlib.util, hashlib
        sp = importlib.util.spec_from_file_location("dfr2", SEAT/"decision_from_retrieval.py")
        dfr2 = importlib.util.module_from_spec(sp); sp.loader.exec_module(dfr2)
        R = dfr2.Retriever(SEAT/".cache"/"section_index_union_20261012.json")
        IX = SEAT/".cache"/"semantic_index_20261012.json"
        if IX.exists(): SV = json.loads(IX.read_text(encoding="utf-8-sig"))["vecs"]
        for _p in (SEAT/".cache").glob("e302s_*.json"):
            try:
                _j = json.loads(_p.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if isinstance(_j.get("v"), list): VC["sha1:" + str(_j.get("text_sha1_20"))] = _j["v"]
        print("   ★证据模式：检索器已载（并集 %d 档）｜语义索引 %d 档" % (len(R.doc2sec), len(SV)))
    rows = []; hit = 0; usage = {}; conf_sum = 0.0
    for it in suite:
        try:
            ev = evidence_for(it["q"], R, SV, VC) if a.evidence else None
            txt, u = ask(it["q"], k, a.model, ev)
        except Exception as ex:
            rows.append({"q": it["q"], "truth": it["truth"], "err": str(ex)[:70]}); continue
        for kk, vv in (u or {}).items():
            if isinstance(vv, (int, float)): usage[kk] = usage.get(kk, 0) + vv
        lab = None; p = None; sc = None
        try:
            s = txt[txt.find("{"): txt.rfind("}")+1]
            j = json.loads(s); lab = j.get("label"); p = float(j.get("p_yes")); sc = int(j.get("score"))
        except Exception:
            pass
        ok_contract = (lab in ("是", "否")) and (p is not None and 0 <= p <= 1) and (sc is not None and 0 <= sc <= 10)
        truth_lab = "是" if it["truth"] else "否"
        good = (lab == truth_lab)
        hit += 1 if good else 0
        if p is not None: conf_sum += max(p, 1-p)
        rows.append({"q": it["q"], "truth": it["truth"], "label": lab, "p_yes": p, "score": sc,
                     "contract": ok_contract, "ok": good, "raw": txt[:60]})
    n = len(rows)
    print("   ── 逐题 ──")
    for r in rows:
        print("   %-24s ｜ 事实=%s ｜ 判=%s ｜ p_yes=%s ｜ score=%s ｜ 契约=%s ｜ %s" % (
            r["q"][:24], "真" if r["truth"] else "假", r.get("label"), r.get("p_yes"), r.get("score"),
            "✓" if r.get("contract") else "✗", "✓" if r.get("ok") else "✗"))
    acc = hit/max(1, n)
    print("   ★★准确率 %d／%d ＝ %.2f ｜ 平均置信度 %.3f ｜ usage=%s" % (hit, n, acc, conf_sum/max(1, n), json.dumps(usage, ensure_ascii=False)))
    print("   ★对照：词面 support 0.70（-1256）｜ 语义阈值 0.50（-1263）｜ concentration 0.50")
    crit = {"①计划之题数与成本上界已给": True, "②真跑时每题皆合契约": all(r.get("contract") for r in rows),
            "③★准确率与词面 0.70 之对照已给出": True}
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "model": a.model,
            "acc": round(acc, 4), "usage": usage, "rows": rows, "criteria": crit}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
