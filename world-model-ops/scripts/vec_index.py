# -*- coding: utf-8 -*-
"""vec_index.py —— 全语料"向量编码"索引之建构器（★默认 dry-run：零调用）
承：-1197（成本勘定：合规档 1102 节≈18.6 万 tokens ⇒ ≲0.2 元）、-1198（旧缓存不可回溯 ⇒ 不省费）、
    -1199（自述缓存 emb_cache：新档含 text_head／src／dim／model）
设计：
  ① build：逐节取 body ⇒ 先查自述缓存（命中免调用）⇒ 未命中者批量嵌入（≤8/批，兼容面之限）
      ⇒ 写 exp/.cache/e302s_*.json（自述）＋ 索文档 exp/.cache/vec_index_<ts>.json（记录 fingerprint／节数／维度／模型）
  ② query：给定查询串 ⇒ 嵌入 ⇒ 与索引逐节余弦 ⇒ 返回 top-k（含节号／档名／分数）
  ③ ★安全：--dry-run 默认；--run 须 --budget-max（元）；预计成本 > 预算 ⇒ 拒绝（宁停不超）
判据（可失败）：①节数与索引档一致；②每节恰一条向量且维度一致；③查询分数单调降；④真跑总费 ≤ 预算
用法：
    python vec_index.py build --index exp/.cache/section_index_20261012_1537.json              # dry-run
    python vec_index.py build --index … --run --budget-max 0.25
    python vec_index.py query --vec exp/.cache/vec_index_<ts>.json --q "撞墙之零重试" --k 5
（中文串一律用「」）
"""
import argparse, json, math, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
EP = "https://api.302ai.cn/v1/embeddings"
PROXY = "http://127.0.0.1:10081"
MODEL = "text-embedding-3-small"
BATCH = 8
PRICE_IN_PER_1K = 0.0002      # ★价目仅为"成本上界"之估（元／1k tokens）；★以账单为准


def key_of(t):
    import hashlib
    return hashlib.sha1(str(t).encode("utf-8")).hexdigest()[:20]


def env_key():
    try:
        for l in ENVF.read_text(encoding="utf-8", errors="replace").splitlines():
            if l.strip().startswith("AI302_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def load_index(p):
    j = json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
    secs = j.get("sections") or []
    return j, secs


def plan(secs):
    ch = sum(len(str(s.get("body") or s.get("text") or "")) for s in secs)
    tok = ch / 1.7
    import pathlib as _p
    cache = SEAT/".cache"
    have = {f.stem for f in cache.glob("e302s_*.json")} if cache.exists() else set()
    hit = 0
    for s in secs:
        body = str(s.get("body") or s.get("text") or "")
        if ("e302s_" + key_of(body)) in have: hit += 1
    miss = len(secs) - hit
    cost = miss * (tok / max(1, len(secs))) / 1000 * PRICE_IN_PER_1K
    return {"sections": len(secs), "chars": ch, "tokens": round(tok, 1),
            "self_cache_hit": hit, "need_embed": miss, "cost_upper_cny": round(cost, 5),
            "batches": (miss + BATCH - 1)//BATCH if miss else 0, "model": MODEL}


def embed_batch(texts, k):
    """★真嵌入（仅 --run 时调用）"""
    import urllib.request
    body = json.dumps({"model": MODEL, "input": texts}, ensure_ascii=False).encode()
    req = urllib.request.Request(EP, data=body, headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=120) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    return [d["embedding"] for d in j.get("data", [])], j.get("usage", {})


def cmd_build(a):
    j, secs = load_index(a.index)
    p = plan(secs)
    print("  ═══ vec_index build ｜ 计划 ═══")
    print("   索引档：%s" % pathlib.Path(a.index).name)
    print("   节 %d ｜ 正文 %d 字符 ｜ 约 %.1f 万 tokens ｜ 模型 %s" % (p["sections"], p["chars"], p["tokens"]/10000, p["model"]))
    print("   ★自述缓存命中 %d ｜ 须嵌入 %d ｜ 批量 %d 次 ｜ ★成本上界 %.5f 元" % (
        p["self_cache_hit"], p["need_embed"], p["batches"], p["cost_upper_cny"]))
    if not a.run:
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）—— 真跑须 --run --budget-max <元>")
        return 0
    if a.budget_max <= 0:
        print("   ★--run 须同时给 --budget-max（正数元）⇒ 拒绝执行（宁停不超）"); return 2
    if p["cost_upper_cny"] > a.budget_max:
        print("   ★成本上界 %.5f 元 > 预算 %.5f 元 ⇒ 拒绝执行（宁停不超）" % (p["cost_upper_cny"], a.budget_max)); return 2
    print("   ★本稿尚未接入真实调用（design draft）⇒ 拒绝 --run（免无据之花销）"); return 3


def cmd_query(a):
    # ★边界处理（2026-10-12 自纠）：索引档不在或不可解析 ⇒ 友好提示并返 2（此前抛未捕获异常）
    vp = pathlib.Path(a.vec)
    if not vp.exists():
        print("   ★索引档不在：%s" % vp.name); return 2
    try:
        v = json.loads(vp.read_text(encoding="utf-8-sig"))
    except Exception as ex:
        print("   ★索引档不可解析：%s" % str(ex)[:80]); return 2
    rows = v.get("rows") or []
    qv = None; shown = 0
    print("  ═══ vec_index query ═══")
    print("   索引：%s ｜ 节 %d ｜ 维度 %s" % (pathlib.Path(a.vec).name, len(rows), v.get("dim")))
    k = env_key()
    if a.run and k:
        vs, usage = embed_batch([a.q], k)
        qv = vs[0]; print("   查询已嵌入（usage=%s）" % json.dumps(usage, ensure_ascii=False))
    if qv is None:
        print("   ⇒ 判：★dry-run（未嵌入查询；亦未算分）—— 真跑须 --run（并扣微量费）")
        return 0
    def cos(x, y):
        s = sum(p_*q_ for p_, q_ in zip(x, y))
        nx = math.sqrt(sum(p_*p_ for p_ in x)); ny = math.sqrt(sum(q_*q_ for q_ in y))
        return s/((nx*ny) or 1e-9)
    sc = [(cos(qv, r["v"]), r.get("doc"), r.get("head", "")) for r in rows if isinstance(r.get("v"), list)]
    sc.sort(key=lambda t: -t[0])
    print("   top%d：" % a.k)
    for s, d, h in sc[:a.k]:
        print("     %.4f ｜ %-38s ｜ %s" % (s, str(d)[:38], str(h)[:44]))
    return 0


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build"); b.add_argument("--index", required=True)
    b.add_argument("--run", action="store_true"); b.add_argument("--budget-max", type=float, default=0.0)
    q = sub.add_parser("query"); q.add_argument("--vec", required=True); q.add_argument("--q", required=True)
    q.add_argument("--k", type=int, default=5); q.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.cmd == "build": return cmd_build(a)
    if a.cmd == "query": return cmd_query(a)
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
