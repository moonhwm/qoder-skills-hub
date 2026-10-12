# -*- coding: utf-8 -*-
"""bailian_probe2.py —— 百炼（DashScope）分模型探活：区分"免费额度专属"与"付费可用"
★目的：403 原话给两条出路（加资金 或 关闭仅用免费额度）；本器以多模型分辨究竟卡在哪一条。
★纪律：凭据零回显；HTTP 200 必读 output.code / error.code；如实分类（429/403/400/200）。
（中文串一律用「」）
"""
import json, pathlib, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HOME = pathlib.Path.home()
env = {}
for line in (HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env").read_text(encoding="utf-8-sig", errors="replace").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
K = env.get("DASHSCOPE_API_KEY", "")
COMPAT = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def call(url, body, to=60):
    r = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=to) as resp:
            return resp.status, round(time.time()-t0, 2), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, round(time.time()-t0, 2), e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return -1, round(time.time()-t0, 2), str(e)[:160]

def brief(payload):
    try:
        j = json.loads(payload)
    except Exception:
        return payload[:130]
    for path in (("error",), ("output",)):
        cur = j
        for p in path:
            cur = cur.get(p) if isinstance(cur, dict) else None
        if isinstance(cur, dict):
            if "code" in cur or "message" in cur:
                return "code=%s ｜ %s" % (cur.get("code"), str(cur.get("message"))[:120])
    if "choices" in j: return "★有 choices（可用）｜usage=%s" % json.dumps(j.get("usage") or {}, ensure_ascii=False)[:60]
    if "data" in j and isinstance(j["data"], list) and j["data"] and "embedding" in (j["data"][0] or {}):
        return "★有 embedding（可用）｜维度 %d" % len(j["data"][0]["embedding"])
    if "output" in j and isinstance(j["output"], dict) and "results" in j["output"]:
        return "★有 results（可用）｜%d 条" % len(j["output"]["results"])
    return json.dumps(j, ensure_ascii=False)[:130]

print("  ═══ ① 聊天（廉价付费档：qwen-turbo／qwen-plus／qwen-max）═══")
for m in ("qwen-turbo", "qwen-plus", "qwen-max"):
    st, dt, tx = call(COMPAT + "/chat/completions", {"model": m, "messages": [{"role": "user", "content": "回一字：好"}], "max_tokens": 8})
    print("   %-12s HTTP %-4s %.2fs ｜ %s" % (m, st, dt, brief(tx)[:110]))
print("  ═══ ② 嵌入（v1／v2／v3／v4）═══")
for m in ("text-embedding-v1", "text-embedding-v2", "text-embedding-v3", "text-embedding-v4"):
    st, dt, tx = call(COMPAT + "/embeddings", {"model": m, "input": ["探活"]})
    print("   %-18s HTTP %-4s %.2fs ｜ %s" % (m, st, dt, brief(tx)[:110]))
print("  ═══ ③ 决策模型与重排（名内之档）═══")
for m in ("decision-model-preview",):
    st, dt, tx = call(COMPAT + "/chat/completions", {"model": m, "messages": [{"role": "user", "content": "是或否：夜色已深"}], "max_tokens": 8})
    print("   %-22s HTTP %-4s %.2fs ｜ %s" % (m, st, dt, brief(tx)[:110]))
for m in ("gte-rerank", "gte-rerank-v2"):
    st, dt, tx = call("https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
                      {"model": m, "input": {"query": "游乐场", "documents": ["夜间游乐场", "股票"]}, "parameters": {"top_n": 1}})
    print("   %-22s HTTP %-4s %.2fs ｜ %s" % (m, st, dt, brief(tx)[:110]))
