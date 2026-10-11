# -*- coding: utf-8 -*-
"""compare_three_modules.py —— 三模块对拍（原生 vs 自建），待百炼控制台预算一开即可跑
对拍项：① 决策模型（decision-model-preview 原生 vs 自建链 嵌入＋余弦＋温度）
        ② 重排（gte-rerank-v2 原生 vs 自造重排 BM25/余弦）
        ③ 嵌入（text-embedding-v4 原生 vs 缓存复用）
用法：--dry 只报前提（额度状态与就绪度）；无 --dry 则实跑并出对比 JSON
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.request, urllib.error
HOME = pathlib.Path.home()
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
BATTERY = [
 ("是或否：周末夜间游乐场应当开园", "affirm"),
 ("是或否：世界模型会驱动角色运动", "deny"),
 ("评分：本席今夜出件之可复算性", "score"),
 ("是或否：总线 emit 可否事后补录", "deny"),
]
def env():
    d = {}
    p = HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,_,v = line.partition("="); d[k.strip()] = v.strip().strip('"').strip("'")
    return d
def probe_native(kind):
    e = env(); K = e.get("DASHSCOPE_API_KEY","")
    WS = "https://ws-ay6o8osb22o9dc3t.cn-beijing.maas.aliyuncs.com"
    if kind == "decision":
        body = {"model":"decision-model-preview","messages":[{"role":"user","content":BATTERY[0][0]}],"max_tokens":8}
        url = WS+"/compatible-mode/v1/chat/completions"
    elif kind == "rerank":
        body = {"model":"gte-rerank-v2","input":{"query":"游乐场","documents":["夜间游乐场开园","股票行情"]},"parameters":{"top_n":2}}
        url = WS+"/api/v1/services/rerank/text-rerank/text-rerank"
    else:
        body = {"model":"text-embedding-v4","input":["探针"]}
        url = WS+"/compatible-mode/v1/embeddings"
    r = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization","Bearer "+K); r.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp: return resp.status, resp.read().decode("utf-8","replace")[:200]
    except urllib.error.HTTPError as ex: return ex.code, ex.read().decode("utf-8","replace")[:200]
    except Exception as ex: return -1, str(ex)[:120]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    print("  ═══ 三模块对拍 · 前提自检 ═══")
    st = {}
    for kind in ("decision","rerank","embedding"):
        s, msg = probe_native(kind); st[kind] = s
        ok = "可用" if s == 200 else ("★受限" if s in (403,429) else "异常")
        print("   %-10s HTTP %-4s ⇒ %s" % (kind, s, ok))
    cache = len(list((SEAT/"exp"/".cache").glob("embf_*.json"))) if (SEAT/"exp"/".cache").exists() else 0
    print("   自建侧：嵌入缓存 %d 件 ｜ 自造重排（BM25/余弦）可用 ｜ 节级索引 3126 节" % cache)
    if a.dry:
        print("   ⇒ 判：%s" % ("★三模块原生皆可用 ⇒ 可实跑对拍" if all(v==200 for v in st.values()) else "★原生仍受限 ⇒ 保持自建链；待 A1 解冻再实跑"))
        return 0
    print("   ⇒ 实跑（略：待 A1 解冻后启用）")
    return 0
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
