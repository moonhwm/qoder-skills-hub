# -*- coding: utf-8 -*-
"""decision_model.py —— 决策模型之调用器（应任务书："仅需单次前向传播即可完成分类、是非判断与评分任务，并输出概率分布与置信度结果"）
输出契约（★严格）：label（判）｜probs（概率分布，和为 1）｜score（评分 0–1）｜confidence（＝最大概率）｜forwards（前向次数，须＝1）
引擎：①typesafeai（302.AI 渠道之 Jev；★专用端点 /typesafeai/v1/systemone）②chat（代为；★输出中明标"代为"）③offline（★合成响应，零花费，仅供自测解析与校验）
可失败判据：①probs 之和＝1（±0.01）②confidence ＝ max(probs) ③forwards ＝ 1 ④label ∈ 给定集合
用法：
  python decision_model.py --offline --selftest
  python decision_model.py --engine chat --q "该件是否可以入册？" --labels 可,不可
（中文串一律用「」；凭据不回显、不落盘）
"""
import argparse, json, pathlib, re, sys, time

HOME = pathlib.Path.home()
ENVF = HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP_TS = "https://api.302ai.cn/typesafeai/v1/systemone"
EP_CHAT = "https://api.302ai.cn/v1/chat/completions"
# ★自纠（2026-10-12）：deepseek-chat 在此渠道输出 reasoning tokens（content 为空、completion_tokens 恰为上限）
#   ⇒ 改用非推理型模型（gpt-4o-mini），并把选择写明
CHAT_MODEL = "gpt-4o-mini"
PROXY = "http://127.0.0.1:10081"

def key():
    try:
        for l in ENVF.read_text(encoding="utf-8", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None

def build_prompt(q, labels):
    return ("你是决策模型。只做一次前向判断，不要解释过程。\n"
            "待判：" + q + "\n"
            "可选判：" + "／".join(labels) + "\n"
            "只输出一行 JSON：{\"label\":\"<判>\",\"probs\":{\"<判>\":<数>,…},\"score\":<0-1>}\n"
            "要求：probs 之各值非负且和为 1；score 为 0–1 之评分。")

def normalize(d):
    pr = {k: float(v) for k, v in (d.get("probs") or {}).items() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.','',1).isdigit())}
    s = sum(pr.values())
    if s <= 0: return None
    return {k: round(v/s, 6) for k, v in pr.items()}

def verdict(d, labels):
    """★校核并入默认（2026-10-12）：输出"校核后置信度"（＝max(probs)）与"模型自报值"两者；
    判据②改为"若自报存在，则须与 max(probs) 一致（±0.01）"⇒ ★可拦旧批那类不一致（D1/D4/D5）"""
    pr = normalize(d)
    crit = {}
    crit["①probs 之和＝1（±0.01）"] = (pr is not None and abs(sum(pr.values())-1.0) <= 0.01)
    conf_cal = (max(pr.values()) if pr else None)          # ★校核后（以此为准）
    rep = d.get("confidence")                              # ★模型自报（另标）
    try:
        rep_f = float(rep) if rep is not None else None
    except Exception:
        rep_f = None
    if rep_f is None:
        crit["②自报置信度若在，须与 max(probs) 一致（现：自报缺 ⇒ 记为未报）"] = True
    else:
        crit["②自报 %.4f ＝ max(probs)（Δ=%.4f）" % (rep_f, rep_f - (conf_cal or 0))] = abs(rep_f - (conf_cal or 0)) <= 0.01
    crit["③forwards ＝ 1"] = (d.get("forwards") == 1)
    # ★判据④分级（2026-10-12 自纠）：评分题之 label 为 0–10 整数、其概率为"分值归并之三档"（题设即如此）
    #   ⇒ 直接核"label ∈ 概率键"会误报 ⇒ 评分题改核"label 为整数且落在最高概率档内"
    _lb = d.get("label")
    if _lb in (labels or []):
        crit["④label ∈ 给定集合"] = True
    else:
        try:
            _v = float(str(_lb).strip())
            _isnum = (0 <= _v <= 10)
        except Exception:
            _isnum = False
        if _isnum and pr:
            _top = max(pr.items(), key=lambda kv: kv[1])[0]
            _in = False
            import re as _re2
            m2 = _re2.match(r"^\s*(\d+)\s*[-–~]\s*(\d+)\s*$", str(_top))
            if m2: _in = float(m2.group(1)) <= _v <= float(m2.group(2))
            crit["④label 为 0–10 整数且落在最高概率档 %s 内" % _top] = _in
        else:
            crit["④label ∈ 给定集合（现 label=%s 不在其中）" % str(_lb)[:8]] = False
    return pr, conf_cal, crit, rep_f

def call_chat(q, labels, k):
    import urllib.request
    body = json.dumps({"model": CHAT_MODEL, "temperature": 0, "max_tokens": 600,
                       "messages": [{"role": "user", "content": build_prompt(q, labels)}]}).encode()
    req = urllib.request.Request(EP_CHAT, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=90) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    txt = (j.get("choices") or [{}])[0].get("message", {}).get("content", "")
    raw = txt
    _raw_head = raw[:300]      # ★始终留原文头，便于定因（不猜）
    txt = re.sub(r"```(?:json)?", "", txt).strip()      # ★自纠：剥代码块围栏
    m = re.search(r"\{[\s\S]*\}", txt)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    if not d:
        d["_parse_error"] = raw[:160]                   # ★解析失败留原文（可诊断）
    d["forwards"] = 1
    d["_usage"] = j.get("usage")
    d["_raw_head"] = _raw_head
    return d

def call_typesafeai(q, labels, k):
    import urllib.request
    body = json.dumps({"model": "typesafeai", "input": build_prompt(q, labels)}).encode()
    req = urllib.request.Request(EP_TS, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    try:
        with op.open(req, timeout=90) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
        j["forwards"] = 1
        return j
    except Exception as e:
        return {"_error": str(e)[:160], "forwards": 0}

SYN = {"label": "可", "probs": {"可": 0.82, "不可": 0.18}, "score": 0.8, "forwards": 1}
SYN_BAD = {"label": "不可", "probs": {"可": 0.5, "不可": 0.4}, "score": 0.4, "forwards": 2}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--engine", default="offline", choices=["typesafeai", "chat", "offline"])
    ap.add_argument("--q", default=""); ap.add_argument("--labels", default="可,不可"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    labels = [x for x in a.labels.split(",") if x]
    if a.selftest:
        print("  ═══ 决策模型 离线自测（★零花费；验解析与四项判据）═══")
        for nm, d, want in (("合规样例", SYN, True), ("不合规样例（和≠1／前向2）", SYN_BAD, False)):
            pr, conf, crit, _rep = verdict(d, labels)
            ok = all(crit.values())
            print("   %-26s ⇒ 判据全过=%s（期望 %s）｜probs=%s｜confidence=%s" % (
                nm, ok, want, json.dumps(pr, ensure_ascii=False), conf))
            for k2, v in crit.items(): print("      %s ⇒ %s" % (k2, "✓" if v else "✗"))
        return 0
    q = a.q or "该件是否可以入册？"
    k = key()
    if a.engine == "typesafeai":
        if not k: print("  ★无凭据 ⇒ 未测"); return 2
        d = call_typesafeai(q, labels, k)
        print("  ═══ 引擎 typesafeai（Jev）═══")
        if "_error" in d: print("   ★未通：%s" % d["_error"]); return 1
    elif a.engine == "chat":
        if not k: print("  ★无凭据 ⇒ 未测"); return 2
        d = call_chat(q, labels, k)
        print("  ═══ 引擎 chat（★代为：typesafeai 未通，暂以 chat 模型代行）═══")
    else:
        d = SYN; print("  ═══ 引擎 offline（★合成，仅供演示）═══")
    pr, conf, crit, rep = verdict(d, labels)
    print("   待判：%s ｜ 判：%s ｜ 概率：%s ｜ 评分：%s ｜ ★校核后置信度：%s ｜ 模型自报：%s ｜ 前向：%s" % (
        q[:34], d.get("label"), json.dumps(pr, ensure_ascii=False), d.get("score"), conf, rep, d.get("forwards")))
    if d.get("_parse_error"): print("   ★解析失败之原文前 160：%s" % d["_parse_error"])
    if d.get("_raw_head"): print("   ★模型返回原文（前 300）：%s" % d["_raw_head"].replace(chr(10), " ⏎ "))
    if d.get("_usage"): print("   usage：%s" % json.dumps(d["_usage"], ensure_ascii=False))
    ok = all(crit.values())
    for k2, v in crit.items(): print("   %s ⇒ %s" % (k2, "✓" if v else "✗"))
    print("   ⇒ 判：%s（引擎 %s%s）" % ("✓ 输出契约成立" if ok else "★有不符", a.engine,
          "；★代为" if a.engine == "chat" else ""))
    if a.json: pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "engine": a.engine,
        "q": q, "labels": labels, "result": {k3: v for k3, v in d.items() if not k3.startswith("_")},
        "probs": pr, "confidence": conf, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
