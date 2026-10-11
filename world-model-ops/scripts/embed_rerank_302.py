# -*- coding: utf-8 -*-
"""embed_rerank_302.py —— 向量编码与重排序（302.AI 为提供方；令条第三模块）
① 编码：POST /v1/embeddings（text-embedding-3-small，1536 维；备 text-embedding-3-large）
② 重排：POST /v1/rerank（jina-reranker-v2-base-multilingual；备 BAAI/bge-reranker-v2-m3）
③ 对拍：同查询同文档下，原生重排 vs 自造重排（余弦）之序对比
用法：python embed_rerank_302.py [--query "<问>"] [--docs "a|b|c"] [--json out.json]
（中文串一律用「」）
"""
import argparse, json, math, pathlib, sys, time, urllib.request, urllib.error

HOME = pathlib.Path.home()
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
EMB = "text-embedding-3-small"; RRK = "jina-reranker-v2-base-multilingual"
DEF_Q = "总线可否事后补录"
DEF_D = ["夜间游乐场开园：以首帧为条件之重绘", "总线 emit 不可事后补录（行为之历史不可伪造）",
         "人设三级 LOD GLB 与四段动画（46/52 通道有效）", "例行复拉与节键重排虚警之自动标注",
         "决策模型单次前向输出概率分布与置信度"]


def env():
    d = {}
    p = HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("="); d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def post(path, body, to=120):
    K = env().get("AI302_API_KEY", "")
    r = urllib.request.Request("https://api.302ai.cn" + path, data=json.dumps(body, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
    for att in range(1, 4):                       # 戒三十四
        try:
            with urllib.request.urlopen(r, timeout=to) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500: return e.code, e.read().decode("utf-8", "replace")[:200]
        except Exception as e:
            if att == 3: return -1, str(e)[:140]
    return -1, "重试耗尽"


def encode(texts):
    st, j = post("/v1/embeddings", {"model": EMB, "input": texts})
    if st != 200 or not isinstance(j, dict): return st, None, j
    return st, [d["embedding"] for d in j["data"]], j.get("usage")


def rerank(q, docs, top=None):
    body = {"model": RRK, "query": q, "documents": docs}
    if top: body["top_n"] = top
    st, j = post("/v1/rerank", body)
    if st != 200 or not isinstance(j, dict): return st, None
    return st, (j.get("results") or j.get("data") or [])


def cos(a, b):
    s = sum(x*y for x, y in zip(a, b))
    return s/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(x*x for x in b)) or 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--query", default=DEF_Q)
    ap.add_argument("--docs", default=""); ap.add_argument("--json", default="")
    a = ap.parse_args()
    q = a.query; docs = a.docs.split("|") if a.docs else DEF_D
    st, V, usage = encode([q] + docs)
    print("  ═══ ① 编码 ⇒ HTTP %s ｜ 条数 %s ｜ usage %s ═══" % (st, len(V) if V else "—", json.dumps(usage or {}, ensure_ascii=False)))
    mine = []
    if V:
        for i, d in enumerate(docs): mine.append((cos(V[0], V[i+1]), d))
        mine.sort(reverse=True)
        print("   ★ 自造重排（余弦）Top3：")
        for s, d in mine[:3]: print("      %.4f ｜ %s" % (s, d[:58]))
    s2, res = rerank(q, docs)
    print("  ═══ ② 原生重排（%s）⇒ HTTP %s ｜ 结果 %s 条 ═══" % (RRK, s2, len(res) if res else "—"))
    nat = []
    if res:
        for r in res:
            idx = r.get("index", r.get("document", {}).get("index") if isinstance(r.get("document"), dict) else None)
            sc = r.get("relevance_score", r.get("score"))
            if isinstance(idx, int) and 0 <= idx < len(docs): nat.append((sc, docs[idx]))
        for sc, d in nat[:3]: print("      %.4f ｜ %s" % (sc or 0, d[:58]))
    if mine and nat:
        top_m = mine[0][1]; top_n = nat[0][1]
        print("  ═══ ③ 对拍 ⇒ 首名%s ═══" % ("★一致" if top_m == top_n else "★不同（自造：%s ／ 原生：%s）" % (top_m[:24], top_n[:24])))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "provider": "302.AI",
            "embed_model": EMB, "rerank_model": RRK, "query": q, "docs": docs,
            "mine_cosine": [{"score": round(s, 4), "doc": d} for s, d in mine],
            "native_rerank": [{"score": s, "doc": d} for s, d in nat]}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   落盘：" + a.json)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
