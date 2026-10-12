# -*- coding: utf-8 -*-
"""decision_rerank.py —— 检索第四臂（cross_encoder 式重排）之★设计稿与骨架
承：-1193 之读记 —— graphiti 之 cross_encoder 有两实现，其 openai 实现为
    "simple boolean classifier prompt ＋ log-probabilities 打分"⇒ 与任务书之"决策模型"（单次前向＋概率分布）同构
    ⇒ 故本臂★复用 decision_model.py（--kind yesno），取 probs["是"] 作分，★零新增模型器物。

接口（照 graphiti 之契约，便于替换）：
    rank(query: str, passages: list[str]) -> list[tuple[str, float]]   # 降序

★安全设计（本稿之要）：
    --dry-run 为★默认：只打印"将调用 N 次、预计输出 tokens 上限、按价目之成本上界"，★绝不发起调用；
    真跑须显式 --run，且须 --budget-max（元）之正数上限；超出即中止（★宁停不超）。

判据（可失败）：
    ①排序单调不增；②每 passage 恰好一次前向（forwards 累计 ＝ passage 数）；
    ③分数 ∈ [0,1] 且 ＝ 该次判定之「是」概率；④真跑时总费用 ≤ --budget-max。

用法：
    python decision_rerank.py --query "…" --passages-file exp/mem/passages.txt --k 10            # dry-run
    python decision_rerank.py --query "…" --passages-file … --run --budget-max 0.02 --json out.json
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent
DM = SEAT/"decision_model.py"

# ★价目（仅用于"成本上界"之估；★以账单为准）
PRICE_PER_1K_OUT = 0.01     # 元／1k 输出 tokens（保守上界，来源：302.AI 之小模型档）
PRICE_PER_1K_IN = 0.001     # 元／1k 输入 tokens（保守上界）


def plan(query, passages, k):
    """只做计划：不发起任何调用"""
    n = len(passages)
    out_tok = n * 8          # ★每 passage 之输出上界（实际应 ≪1 token 级之判定 ＋ 少量）
    in_tok = n * (len(query) // 2 + 60)
    cost = out_tok / 1000 * PRICE_PER_1K_OUT + in_tok / 1000 * PRICE_PER_1K_IN
    return {"calls": n, "top_k": k, "out_tokens_upper": out_tok, "in_tokens_upper": in_tok,
            "cost_upper_cny": round(cost, 5), "engine": "decision_model.py --kind yesno",
            "score_source": "probs[「是」]"}


def rank_dry(query, passages, k):
    """★dry-run：给出计划与"将执行之形态"，★不调用 API；排序以输入序占位并显式标注"""
    p = plan(query, passages, k)
    rows = [{"i": i, "passage_head": (t[:60] + "…") if len(t) > 60 else t, "score": None} for i, t in enumerate(passages[:k])]
    return p, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--passages-file", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--run", action="store_true", help="★须显式开启；默认 dry-run（零调用）")
    ap.add_argument("--budget-max", type=float, default=0.0, help="元；--run 时必填且 >0")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    pf = pathlib.Path(a.passages_file)
    if not pf.exists():
        print("   ★passages-file 不在：%s" % pf); return 2
    passages = [l.strip() for l in pf.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    print("  ═══ decision_rerank（第四臂·cross_encoder 式）═══")
    print("   接口：rank(query, passages) -> [(passage, score)] ★降序（照 graphiti 之契约）")
    print("   引擎：%s ｜ 分数来源：%s" % ("decision_model.py --kind yesno", "probs[「是」]"))
    print("   passages：%d 条 ｜ top_k：%d" % (len(passages), a.k))
    p, rows = rank_dry(a.query, passages, a.k)
    print("   ★计划：将调用 %d 次（每 passage 一次前向）｜ 输出 tokens 上界 %d ｜ 输入上界 %d ｜ ★成本上界 %.5f 元" % (
        p["calls"], p["out_tokens_upper"], p["in_tokens_upper"], p["cost_upper_cny"]))
    if not a.run:
        print("   ⇒ 判：★dry-run（未调用任何 API；零费用）—— 真跑须 --run --budget-max <元>")
        print("   ★将执行之形态（占位，未打分）：")
        for r in rows[:min(5, len(rows))]:
            print("      i=%-3d score=—  ｜ %s" % (r["i"], r["passage_head"]))
        if a.json:
            pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "mode": "dry-run", "plan": p, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        return 0
    # ★真跑分支（本稿预留；须预算与闸）
    if a.budget_max <= 0:
        print("   ★--run 须同时给 --budget-max（正数元）⇒ 拒绝执行（宁停不超）"); return 2
    if p["cost_upper_cny"] > a.budget_max:
        print("   ★成本上界 %.5f 元 > 预算 %.5f 元 ⇒ 拒绝执行（宁停不超）" % (p["cost_upper_cny"], a.budget_max)); return 2
    print("   ⇒ 判：★本稿尚未接入真实调用（design draft）⇒ 拒绝 --run（免无据之花销）")
    print("   ★接入方式（下一步）：逐 passage 调 decision_model.py 之 call_chat(--kind yesno)，累计 forwards 与费用，超限即停")
    return 3


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
