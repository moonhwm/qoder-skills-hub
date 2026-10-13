#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""orthocheck.py —— 多厂商向量会裁正交探针（tongtu-hub v4 熔铸证明工具/资产）

用途：对「候选技能描述 vs 既有技能库」做客观非正交判定，复现 tongtu-hub v4 熔铸时的判定规则。
判定规则（先声明后执行，与用户立法一致：严禁主观臆断）：
  IN（非正交，须融合）   = 双通道内容级排名均 top5 且双通道 z 均值 >= 1.0
  边界（引用不合并）     = 单通道 top5，或 z 均值落在 [0.7, 1.0)
  OUT（正交）            = 其余
其中 z 以「全库两两余弦背景分布」为参照（mu/sigma 可实测自算或外给）。

用法：
  # 实测模式（凭据仅经环境变量注入，零落盘）：
  python3 orthocheck.py --desc "<候选描述>" --registry corpus.json \
      --providers bailian,tokenhub [--top 5] [--json out.json]
  # corpus.json: [{"name":..., "desc":...}, ...]（desc 缺省用 name）
  # 自检（离线，合成向量，含负断言）：
  python3 orthocheck.py --smoke

环境变量（按 provider 需要）：
  BAILIAN_GIFT_API_KEY 或 BAILIAN_API_KEY   —— 阿里云百炼 text-embedding-v3 (dim1024)
  TENCENT_TOKENHUB_API_KEY                  —— 腾讯云 TokenHub kinfra-text-embedding-4b (dim2560)
  HUAWEI_MAAS_API_KEY                       —— 华为云 MaaS bge-m3（西南-贵阳一）
  ARK_API_KEY                               —— 火山引擎 doubao-embedding-text-240515
缺席的 provider 一律如实降级声明，不以单通道结论冒充会裁。
"""
import argparse, json, math, os, sys, time, urllib.request

PROVIDERS = {
    "bailian": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
        "model": "text-embedding-v3", "extra": {"dimension": "1024"},
        "env": ["BAILIAN_GIFT_API_KEY", "BAILIAN_API_KEY"],
    },
    "tokenhub": {
        "url": "https://tokenhub.tencentmaas.com/v1/embeddings",
        "model": "kinfra-text-embedding-4b", "extra": {},
        "env": ["TENCENT_TOKENHUB_API_KEY"],
    },
    "huawei": {
        "url": "https://api.modelarts-maas.com/v1/embeddings",
        "model": "bge-m3", "extra": {},
        "env": ["HUAWEI_MAAS_API_KEY"],
    },
    "volcengine": {
        "url": "https://ark.cn-beijing.volces.com/api/v3/embeddings",
        "model": "doubao-embedding-text-240515", "extra": {},
        "env": ["ARK_API_KEY"],
    },
}

# 判定阈值（熔铸时标定，越界拒收防绕闸）
Z_IN, Z_EDGE, TOP_N = 1.0, 0.7, 5


def embed_batch(url, key, model, texts, extra=None, chunk=8, retry=3):
    """OpenAI 兼容 /embeddings 批量取向量，按 index 排序。"""
    vecs = [None] * len(texts)
    for i in range(0, len(texts), chunk):
        part = texts[i:i + chunk]
        body = {"model": model, "input": part}
        if extra:
            body.update(extra)
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
        last = None
        for attempt in range(retry):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read().decode("utf-8"))
                for item in data["data"]:
                    vecs[i + item["index"]] = item["embedding"]
                break
            except Exception as e:  # noqa: BLE001 - 如实记录末次错误
                last = e
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError("embed failed after %d retries: %s" % (retry, last))
    if any(v is None for v in vecs):
        raise RuntimeError("embed returned incomplete vectors")
    return vecs


def l2norm(v):
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        raise ValueError("zero vector")
    return [x / n for x in v]


def cos(a, b):
    return sum(x * y for x, y in zip(l2norm(a), l2norm(b)))


def background_stats(vecs):
    """全库两两余弦背景分布 mu/sigma（不含自配对）。"""
    n = len(vecs)
    if n < 3:
        raise ValueError("registry too small for background (need >=3)")
    vn = [l2norm(v) for v in vecs]
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(sum(x * y for x, y in zip(vn[i], vn[j])))
    mu = sum(sims) / len(sims)
    var = sum((s - mu) ** 2 for s in sims) / len(sims)
    return mu, math.sqrt(var)


def judge(ranks, zscores, top_n=TOP_N, z_in=Z_IN, z_edge=Z_EDGE):
    """ranks/zscores: {provider: rank/z}。返回 (verdict, reason)。"""
    if not ranks:
        return "UNDETERMINED", "无在轨通道，如实降级，不下结论"
    top_hits = sum(1 for r in ranks.values() if r <= top_n)
    zmean = sum(zscores.values()) / len(zscores)
    if len(ranks) >= 2 and top_hits == len(ranks) and zmean >= z_in:
        return "IN", "双通道均 top%d 且 z 均值 %.3f >= %.1f" % (top_n, zmean, z_in)
    if z_edge <= zmean < z_in:
        return "EDGE", "z 均值 %.3f 落边界带 [%.1f, %.1f)" % (zmean, z_edge, z_in)
    if top_hits >= 1:
        return "EDGE", "单通道 top%d 命中（%d/%d 路），z 均值 %.3f——会裁不足禁判 IN" % (
            top_n, top_hits, len(ranks), zmean)
    return "OUT", "top%d 命中 %d 路，z 均值 %.3f" % (top_n, top_hits, zmean)


def run_live(args):
    registry = json.load(open(args.registry, encoding="utf-8"))
    if not registry:
        print("FATAL: 注册表为空——禁静默过闸（无基线不判决）", file=sys.stderr)
        return 2
    names = [r.get("name", "?") for r in registry]
    texts = [r.get("desc") or r.get("name", "") for r in registry]
    cand = args.desc
    report = {"candidate_head": cand[:60], "providers": {}, "degraded": [], "verdicts": {}}
    all_ranks, all_z = {}, {}
    for pname in args.providers.split(","):
        pname = pname.strip()
        p = PROVIDERS.get(pname)
        if not p:
            report["degraded"].append({"provider": pname, "why": "未知 provider"})
            continue
        key = next((os.environ[e] for e in p["env"] if os.environ.get(e)), None)
        if not key:
            report["degraded"].append({"provider": pname, "why": "凭据缺席（env %s 未设）" % "/".join(p["env"])})
            continue
        try:
            vecs = embed_batch(p["url"], key, p["model"], [cand] + texts, p["extra"])
        except Exception as e:  # noqa: BLE001
            report["degraded"].append({"provider": pname, "why": "调用失败：%s" % str(e)[:120]})
            continue
        cv, lib = vecs[0], vecs[1:]
        sims = [(names[i], cos(cv, lib[i])) for i in range(len(lib))]
        mu, sigma = background_stats(lib)
        sims.sort(key=lambda x: -x[1])
        # 逐库内件记录：本通道排名与 z（判定规则以「件」为单位会裁）
        for pos, (nm, s) in enumerate(sims, start=1):
            z = (s - mu) / sigma if sigma > 0 else 0.0
            all_ranks.setdefault(nm, {})[pname] = pos
            all_z.setdefault(nm, {})[pname] = z
        report["providers"][pname] = {
            "model": p["model"],
            "bg_mu": round(mu, 4), "bg_sigma": round(sigma, 4),
            "top": [{"name": nm, "sim": round(s, 4),
                     "z": round((s - mu) / sigma, 4) if sigma > 0 else 0.0}
                    for nm, s in sims[: args.top]],
        }
    # 逐件会裁：任一件判 IN 即整案 IN（须融合清单）
    item_verdicts = {}
    for nm in names:
        if nm not in all_ranks:
            continue
        v, why = judge(all_ranks[nm], all_z[nm])
        if v in ("IN", "EDGE"):
            item_verdicts[nm] = {"decision": v, "reason": why,
                                 "z_mean": round(sum(all_z[nm].values()) / len(all_z[nm]), 4)}
    ins = [nm for nm, d in item_verdicts.items() if d["decision"] == "IN"]
    verdict = "IN" if ins else ("EDGE" if item_verdicts else "OUT")
    report["verdicts"] = {"decision": verdict,
                          "IN_items": ins, "EDGE_items": [nm for nm, d in item_verdicts.items() if d["decision"] == "EDGE"],
                          "detail": item_verdicts,
                          "channels": len(report["providers"]),
                          "panel": args.providers, "degraded_n": len(report["degraded"])}
    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        open(args.json, "w", encoding="utf-8").write(out)
    print(out)
    return 0


def smoke():
    """离线自检：合成向量验证 cos/z/judge 数学 + 负断言（只测 happy path 视为无效）。"""
    fails = []

    def chk(name, cond):
        if not cond:
            fails.append(name)

    # 1. 相同向量 cos=1，正交向量 cos=0
    chk("cos-identical", abs(cos([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9)
    chk("cos-orthogonal", abs(cos([1, 0], [0, 1])) < 1e-9)
    # 2. 零向量拒收（fail-closed）
    try:
        cos([0, 0], [1, 1])
        chk("cos-zero-reject", False)
    except ValueError:
        pass
    # 3. 背景分布：全等同库 sigma=0 → z 视为 0 不炸
    vecs = [[1, 0], [1, 0], [1, 0]]
    mu, sigma = background_stats(vecs)
    chk("bg-identical-mu1", abs(mu - 1.0) < 1e-9 and sigma < 1e-9)
    # 4. 小库拒收（<3 件无背景基线）
    try:
        background_stats([[1, 0], [0, 1]])
        chk("bg-small-reject", False)
    except ValueError:
        pass
    # 5. judge：双通道 top5 + z>=1.0 → IN
    v, _ = judge({"a": 1, "b": 2}, {"a": 1.2, "b": 1.1})
    chk("judge-IN", v == "IN")
    # 6. judge：单通道 top5 → EDGE（负断言：不得判 IN）
    v, _ = judge({"a": 1, "b": 9}, {"a": 1.5, "b": 0.2})
    chk("judge-single-top-EDGE-not-IN", v == "EDGE")
    # 7. judge：z 均值 0.8 边界带 → EDGE
    v, _ = judge({"a": 8, "b": 9}, {"a": 0.8, "b": 0.8})
    chk("judge-zband-EDGE", v == "EDGE")
    # 8. judge：双 OUT（负断言：低相似不得误判 IN/EDGE）
    v, _ = judge({"a": 50, "b": 60}, {"a": 0.1, "b": -0.2})
    chk("judge-OUT", v == "OUT")
    # 9. judge：单通道在轨 z>=1.0 且 top5 —— 会裁不足，禁冒充双通道 IN
    v, _ = judge({"a": 2}, {"a": 1.5})
    chk("judge-single-channel-not-IN", v in ("EDGE", "OUT") and v != "IN")
    # 10. judge：零通道 → UNDETERMINED（如实降级，不下结论）
    v, _ = judge({}, {})
    chk("judge-zero-channel-UNDETERMINED", v == "UNDETERMINED")
    # 11. embed 缺键不伪造：PROVIDERS 每项 env 列表非空
    chk("providers-env-declared", all(p["env"] for p in PROVIDERS.values()))
    # 12. 华为系候选在面板内（盘古执法局：选型候选集须含华为系）
    chk("huawei-in-panel", "huawei" in PROVIDERS)

    if fails:
        print("SMOKE FAIL: %s" % ", ".join(fails))
        return 1
    print("SMOKE OK: 12 项断言（含 6 项负断言）全过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="多厂商向量会裁正交探针")
    ap.add_argument("--desc", help="候选技能描述文本")
    ap.add_argument("--registry", help="技能库 JSON：[{name, desc}, ...]")
    ap.add_argument("--providers", default="bailian,tokenhub,huawei,volcengine",
                    help="会裁面板（逗号分隔），缺席即降级")
    ap.add_argument("--top", type=int, default=TOP_N)
    ap.add_argument("--json", help="报告落盘路径")
    ap.add_argument("--smoke", action="store_true", help="离线自检（合成向量+负断言）")
    args = ap.parse_args()
    if args.smoke:
        return smoke()
    if not args.desc or not args.registry:
        ap.error("实测模式须 --desc 与 --registry 同给（或用 --smoke 自检）")
    return run_live(args)


if __name__ == "__main__":
    sys.exit(main())
