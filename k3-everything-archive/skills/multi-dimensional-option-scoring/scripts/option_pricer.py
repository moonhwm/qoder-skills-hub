#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
option_pricer.py — Black-Scholes 变体期权化估值工具（纯标准库）

将"远期价值选项"视为欧式看涨期权定价：

    C = S·N(d1) − K·e^(−rT)·N(d2)
    d1 = (ln(S/K) + (r + σ²/2)·T) / (σ·√T)
    d2 = d1 − σ·√T

N(x) 用 math.erf 实现：N(x) = 0.5·(1 + erf(x/√2))

参数定义模板（四参数来源必须在报告中显式声明）：
  S     标的现值：多因子合成（如可比交易价、现金流折现、市场容量×份额），
        需列出各因子权重与 conf 等级
  K     进入成本：获取该选项所需支付的全部成本（金钱、时间机会成本折算）
  T     时间窗口：从现在到价值兑现/退出节点的年数（可分数）
  sigma 波动率 σ：多源波动率合成（历史波动、同类资产波动、情景离散度），
        默认取各来源的加权均方根
  r     无风险利率（可选，默认 0.03）

输出：期权价值 C、内在价值、时间价值、Delta = N(d1)，以及 d1/d2 便于复核。

用法：
  python3 option_pricer.py --S 100 --K 90 --T 2 --sigma 0.35
  python3 option_pricer.py --S 100 --K 90 --T 2 --sigma 0.35 --r 0.05 --json
  python3 option_pricer.py --help
"""

import argparse
import json
import math
import sys


def norm_cdf(x):
    """标准正态累积分布函数，用 math.erf 实现。"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(S, K, T, sigma, r):
    """返回 (C, d1, d2, delta)。T<=0 时退化为内在价值。"""
    if T <= 0:
        C = max(0.0, S - K)
        delta = 1.0 if S > K else 0.0
        return C, float("nan"), float("nan"), delta
    if sigma <= 0:
        # 无波动退化为确定性贴现
        fwd = S - K * math.exp(-r * T)
        C = max(0.0, fwd)
        delta = 1.0 if fwd > 0 else 0.0
        return C, float("nan"), float("nan"), delta
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    C = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    delta = norm_cdf(d1)
    return C, d1, d2, delta


def main():
    p = argparse.ArgumentParser(
        description="Black-Scholes 变体期权化估值：C = S·N(d1) − K·e^(−rT)·N(d2)，N(x) 用 math.erf 实现。"
    )
    p.add_argument("--S", type=float, required=True,
                   help="标的现值（多因子合成，>0）")
    p.add_argument("--K", type=float, required=True,
                   help="进入成本 / 行权价（>0）")
    p.add_argument("--T", type=float, required=True,
                   help="时间窗口，单位年（>=0，可分数）")
    p.add_argument("--sigma", type=float, required=True,
                   help="波动率 σ（多源合成，>=0）")
    p.add_argument("--r", type=float, default=0.03,
                   help="无风险利率（默认 0.03）")
    p.add_argument("--json", action="store_true",
                   help="以机器可读 JSON 输出")
    args = p.parse_args()

    if args.S <= 0:
        p.error("--S 必须 > 0")
    if args.K <= 0:
        p.error("--K 必须 > 0")
    if args.T < 0:
        p.error("--T 必须 >= 0")
    if args.sigma < 0:
        p.error("--sigma 必须 >= 0")

    C, d1, d2, delta = bs_call(args.S, args.K, args.T, args.sigma, args.r)
    intrinsic = max(0.0, args.S - args.K)
    time_value = max(0.0, C - intrinsic)

    result = {
        "inputs": {"S": args.S, "K": args.K, "T": args.T,
                   "sigma": args.sigma, "r": args.r},
        "option_value": round(C, 4),
        "intrinsic_value": round(intrinsic, 4),
        "time_value": round(time_value, 4),
        "delta": round(delta, 4),
        "d1": None if math.isnan(d1) else round(d1, 4),
        "d2": None if math.isnan(d2) else round(d2, 4),
    }

    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print("Black-Scholes 变体估值结果")
        print("  输入: S=%.4f K=%.4f T=%.4f σ=%.4f r=%.4f"
              % (args.S, args.K, args.T, args.sigma, args.r))
        print("  期权价值 C   = %.4f" % result["option_value"])
        print("  内在价值     = %.4f" % result["intrinsic_value"])
        print("  时间价值     = %.4f" % result["time_value"])
        print("  Delta N(d1)  = %.4f" % result["delta"])
        if d1 == d1:  # 非 NaN
            print("  d1 = %.4f, d2 = %.4f" % (d1, d2))


if __name__ == "__main__":
    main()
