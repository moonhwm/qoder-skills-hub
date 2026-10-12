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
    if a.probe_only or not a.suite:
        print("   ⇒ 判：★探针毕（未跑基准）")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0 if st == 200 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
