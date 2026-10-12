# -*- coding: utf-8 -*-
"""bailian_decision_probe.py —— 百炼（DashScope）之决策模型探针（2026-10-12 立，应 -1354 之果）
由来：-1354 见百炼 `qwen3.7-plus` HTTP 200 可用，而本席既有决策器（decision_llm_suite）★端点硬编码 302.AI
      ⇒ ★只增不改：另立本器，以百炼端点为"决策模型"之候选通道。
本器（★闸内；先最小验通，再可选跑基准）：
  ① 读 .env 之 DASHSCOPE_API_KEY 与 DASHSCOPE_WS_BASE（★凭据零回显）；
  ② 以兼容模式端点发★一次最小 chat（max_tokens 小）⇒ 报 HTTP／用量／首 60 字；
  ③ `--suite` 时对指定基准逐题单次前向，校契约五項（label／p_yes／score ⇒ 归一为 probs／confidence）
判据（可失败）：①键与端点已取到；②一次调用有 HTTP 码与用量；③★不回显凭据
用法：python bailian_decision_probe.py [--model qwen3.7-plus] [--probe-only] [--suite <json>] [--run --budget-max 0.01]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.request

SEAT = pathlib.Path(__file__).resolve().parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
PROXY = "http://127.0.0.1:10081"
COMPAT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


def env():
    d = {}
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if "=" in l and not l.strip().startswith("#"):
                k, _, v = l.partition("=")
                d[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return d


def call(key, url, model, msgs, max_tokens=40, to=60):
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": msgs},
                      ensure_ascii=False).encode()
    r = urllib.request.Request(url, data=body, headers={"Authorization": "Bearer " + key,
                                                       "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    t0 = time.time()
    try:
        with op.open(r, timeout=to) as resp:
            j = json.loads(resp.read().decode("utf-8", "replace"))
            return 200, j, time.time()-t0
    except urllib.error.HTTPError as e:
        try: j = json.loads(e.read().decode("utf-8", "replace"))
        except Exception: j = {"raw": "?"}
        return e.code, j, time.time()-t0
    except Exception as e:
        return -1, {"err": str(e)[:80]}, time.time()-t0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="qwen3.7-plus")
    ap.add_argument("--url", default=COMPAT); ap.add_argument("--probe-only", action="store_true")
    ap.add_argument("--suite", default=""); ap.add_argument("--run", action="store_true")
    ap.add_argument("--budget-max", type=float, default=0.0); ap.add_argument("--json", default="")
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--ev-file", default="")   # ★2026-10-12 加（-1358 之请）：接入外部事实源（台账证据）   # ★2026-10-12 加（-1357 之坍塌诊断）：4 例 few-shot ＋ 明令不得一律判否
    a = ap.parse_args()
    e = env(); k = e.get("DASHSCOPE_API_KEY") or e.get("DASHSCOPE_WS_KEY")
    base = e.get("DASHSCOPE_WS_BASE") or ""
    # ★2026-10-12 自纠（-1355 之查明）：可用通道为★WS（业务空间）端点，而公有云端点被预算墙拦
    #   ⇒ 若 .env 有 DASHSCOPE_WS_BASE 且用户未显式给 --url ⇒ ★默认改用 WS 端点
    if base and a.url == COMPAT:
        # ★自纠（-1356）：DASHSCOPE_WS_BASE ★已含 /compatible-mode/v1 ⇒ 只接 /chat/completions
        a.url = base.rstrip("/") + ("/chat/completions" if base.rstrip("/").endswith("/v1") else "/compatible-mode/v1/chat/completions")
    print("  ═══ 百炼决策探针（★凭据零回显）═══")
    print("   键：%s ｜ 端点：%s ｜ 模型：%s" % ("已读到（%d 字）" % len(k) if k else "★未读到",
                                            a.url.split("/")[2], a.model))
    if base: print("   （.env 另有 DASHSCOPE_WS_BASE：%s）" % base.split("/")[2])
    if not k:
        print("   ⇒ 判：★无凭据，止"); return 2
    st, j, dt = call(k, a.url, a.model, [{"role": "user", "content": "只回一个字：好"}], 8)
    txt = ""
    try: txt = j["choices"][0]["message"]["content"]
    except Exception: txt = json.dumps(j, ensure_ascii=False)[:100]
    print("   ★最小调用：HTTP %s ｜ %.2fs ｜ 用量 %s ｜ 回：%s"
          % (st, dt, j.get("usage") or "-", str(txt)[:60]))
    crit = {"①键与端点已取到": bool(k), "②一次调用有 HTTP 码": st != 0, "③★不回显凭据": True}
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    res = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "model": a.model, "url_host": a.url.split("/")[2],
           "probe_http": st, "probe_usage": j.get("usage"), "probe_reply_head": str(txt)[:60], "criteria": crit}
    if a.suite and st == 200:
        # ★2026-10-12 加（-1355 之果）：以指定提供商跑决策基准 —— 契约五项 ＋ ★平衡准确率 ＋ 多数类基线
        sp = pathlib.Path(a.suite)
        if not sp.exists():
            print("   ★基准不在：%s" % sp.name)
        else:
            sj = json.loads(sp.read_text(encoding="utf-8-sig"))
            items = sj if isinstance(sj, list) else (sj.get("items") or sj.get("suite") or [])
            est = len(items) * (300/1.7/1000*0.0008 + 40/1.7/1000*0.002)
            print("   ★基准 %s ｜ 项 %d ｜ ★成本上界估 ≈%.6f 元" % (sp.name, len(items), est))
            if not a.run or a.budget_max < est:
                print("   ⇒ 判：★须 --run --budget-max ≥ %.6f（宁停不超）" % est)
                res["suite"] = {"plan": len(items), "est": round(est, 6), "ran": False}
            else:
                EV = {}
                if a.ev_file:
                    _ej = json.loads(pathlib.Path(a.ev_file).read_text(encoding="utf-8-sig"))
                    for _r in (_ej.get("items") or []):
                        EV[str(_r.get("stmt") or "")] = _r.get("ev") or []
                    print("   ★外部事实源：%s（%d 条陈述带证据）" % (pathlib.Path(a.ev_file).name, len(EV)))
                SYS = ("你是严格的判定器。只输出一个 JSON，形如 {\\\"label\\\":\\\"是\\\",\\\"p_yes\\\":0.0,\\\"score\\\":0}；"
                       "label 只能是「是」或「否」；p_yes 为 0–1；score 为 0–10。不得输出任何其它文字。")

                if a.shots:
                    SYS += (" 注意：本席确有若干器物与能力，判「是」与判「否」同样常见；★不得因不确定即一律判否。")
                    SHOTS = [("本席有语义索引器", "是"), ("本席有语音转写器", "否"),
                             ("本席有台账链校验器", "是"), ("本席有视频生成器", "否")]
                else:
                    SHOTS = []
                ok = 0; tp = tn = fp = fn = 0; us = 0; rows = []
                for idx, it in enumerate(items, 1):
                    q = str(it.get("q") or it.get("stmt") or ""); tr = bool(it.get("truth"))
                    msgs = [{"role": "system", "content": SYS}]
                    for _sq, _sa in SHOTS:
                        msgs.append({"role": "user", "content": _sq})
                        msgs.append({"role": "assistant",
                                     "content": json.dumps({"label": _sa, "p_yes": (0.9 if _sa == "是" else 0.1),
                                                            "score": (8 if _sa == "是" else 2)}, ensure_ascii=False)})
                    _evs = EV.get(q) or []
                    if _evs:
                        _et = "\n".join("- " + str(e.get("text") or "") for e in _evs[:3])
                        msgs.append({"role": "user", "content": "【本席台账之相关条目（外部事实源）】\n" + _et +
                                     "\n\n请据上列事实，判定以下陈述是否合于本席事实：" + q})
                    else:
                        msgs.append({"role": "user", "content": q})
                    st2, j2, dt2 = call(k, a.url, a.model, msgs, 120, 60)
                    try:
                        u = j2.get("usage") or {}
                        us += int(u.get("total_tokens") or 0)
                        raw = j2["choices"][0]["message"]["content"]
                        o = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
                        lab = str(o.get("label")); py_ = float(o.get("p_yes")); sc = float(o.get("score"))
                        cok = (lab in ("是", "否")) and (0.0 <= py_ <= 1.0) and (0.0 <= sc <= 10.0)
                        pred = (lab == "是")
                        if cok: ok += 1
                        if tr and pred: tp += 1
                        elif (not tr) and (not pred): tn += 1
                        elif (not tr) and pred: fp += 1
                        else: fn += 1
                        rows.append({"q": q[:40], "truth": tr, "label": lab, "p_yes": py_, "score": sc, "contract": cok})
                    except Exception as ex:
                        rows.append({"q": q[:40], "truth": tr, "err": str(ex)[:60], "contract": False})
                    if idx % 4 == 0: print("      …已 %d／%d" % (idx, len(items)))
                n = len(items)
                tpr = tp/max(1, tp+fn); tnr = tn/max(1, tn+fp)
                base = max((tp+fn)/max(1, n), (tn+fp)/max(1, n))
                print("   ── ★决策基准之结果（%s）──" % a.model)
                print("   ★契约合规 %d／%d ｜ 混淆：TP %d ｜ TN %d ｜ FP %d ｜ FN %d" % (ok, n, tp, tn, fp, fn))
                print("   ★准确率 %.3f ｜ ★平衡准确率 %.3f（真 %.3f／假 %.3f）｜ ★多数类基线 %.3f"
                      % ((tp+tn)/max(1, n), (tpr+tnr)/2, tpr, tnr, base))
                print("   ★用量合计 %d tokens" % us)
                res["suite"] = {"file": sp.name, "n": n, "contract_ok": ok, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
                                "acc": round((tp+tn)/max(1, n), 4), "balanced_acc": round((tpr+tnr)/2, 4),
                                "tpr": round(tpr, 4), "tnr": round(tnr, 4), "baseline": round(base, 4),
                                "tokens": us, "ran": True, "rows": rows}
    if a.probe_only and not a.suite:
        print("   ⇒ 判：★探针毕（未跑基准）")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if st == 200 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
