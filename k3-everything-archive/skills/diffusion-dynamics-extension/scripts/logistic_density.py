#!/usr/bin/env python3
"""Logistic 增长 + 一维扩散密度场数值模拟（纯标准库，显式有限差分）。

模型方程（Fisher-KPP 型反应扩散方程加源项与损耗项）：
    ∂ρ/∂t = D·∇²ρ + r·ρ·(1 - ρ/K) + S - L
  ρ = 密度场（如一维空间上的用户密度、产业密度、植被覆盖度）
  D = 扩散系数，r = 内禀增长率，K = 承载力
  S = 外部源项（常数或逐格数组），L = 损耗项（常数或逐格数组）

适用：密度场的长期演化、区域渗透、分布前沿推进速度估计。
数值方法：一维显式有限差分 + 自动子步进保证稳定性 (D·dt/dx² <= 0.4)。

输入：stdin JSON：
{
  "n": 101, "dx": 1.0, "D": 0.5, "r": 0.2, "K": 1.0,
  "S": 0.0, "L": 0.0,                    // 可为数值或长度 n 的数组
  "days": 100, "dt": 0.1,
  "initial": {"type": "point", "position": 50, "mass": 0.1},
             // type: point | uniform(value) | custom(values 数组)
  "intervention": {                       // 可选，双情景对比
    "start_day": 40,
    "overrides": {"D": 0.2, "r": 0.1, "S": 0.0, "L": 0.01}
  }
}
输出：stdout JSON：
  {"params": ..., "stability": {...},
   "timeseries": [{"day","total_mass","max_density","front_position"}...],
   "final_profile": [...],                // 逐日终态密度剖面
   "front_velocity_estimate": ...}        // 前沿推进速度（格/天）
  双情景时输出 baseline / intervention / effect（终态总量差、前沿差）。
"""

import argparse
import json
import sys


def as_field(v, n, name):
    """把标量或长度 n 的数组统一为长度 n 的 list。"""
    if isinstance(v, list):
        if len(v) != n:
            raise ValueError("%s 数组长度须为 n=%d" % (name, n))
        return [float(x) for x in v]
    return [float(v)] * n


def make_initial(cfg, n, dx):
    t = cfg.get("type", "point")
    rho = [0.0] * n
    if t == "point":
        pos = int(cfg.get("position", n // 2))
        if not 0 <= pos < n:
            raise ValueError("point.position 越界")
        rho[pos] = float(cfg.get("mass", 0.1)) / dx
    elif t == "uniform":
        rho = [float(cfg.get("value", 0.1))] * n
    elif t == "custom":
        vals = cfg.get("values")
        if not isinstance(vals, list) or len(vals) != n:
            raise ValueError("custom.values 须为长度 n 的数组")
        rho = [float(x) for x in vals]
    else:
        raise ValueError("initial.type 须为 point/uniform/custom")
    return rho


def step(rho, D, r, K, S, L, dx, dt):
    """单步显式差分：扩散(零通量边界) + logistic 增长 + 源 - 损耗。"""
    n = len(rho)
    lap = [0.0] * n
    for i in range(n):
        left = rho[i - 1] if i > 0 else rho[i]        # 零通量边界
        right = rho[i + 1] if i < n - 1 else rho[i]
        lap[i] = (left - 2.0 * rho[i] + right) / (dx * dx)
    out = [0.0] * n
    for i in range(n):
        dr = D * lap[i] + r * rho[i] * (1.0 - rho[i] / K) + S[i] - L[i]
        out[i] = max(0.0, rho[i] + dr * dt)           # 密度不可为负
    return out


def run(rho, D, r, K, S, L, dx, dt, days):
    """积分 days 天，内部自动子步进保证 D·h/dx² <= 0.4。返回逐日摘要与终态。"""
    n = len(rho)
    if D > 0:
        h_max = 0.4 * dx * dx / D
        n_sub = max(1, int(dt / h_max) + 1)
    else:
        n_sub = 1
    h = dt / n_sub
    front_threshold = 0.01 * K
    series = []
    steps = int(round(days / dt))
    for k in range(steps + 1):
        front = -1
        for i in range(n - 1, -1, -1):
            if rho[i] > front_threshold:
                front = i
                break
        series.append({
            "day": round(k * dt, 4),
            "total_mass": round(sum(rho) * dx, 6),
            "max_density": round(max(rho), 6),
            "front_position": front,
        })
        if k == steps:
            break
        for _ in range(n_sub):
            rho = step(rho, D, r, K, S, L, dx, h)
    return series, rho, h, n_sub


def front_velocity(series):
    """用起止前沿位置估计平均推进速度（格/天）。"""
    start = next((p for p in series if p["front_position"] >= 0), None)
    if start is None:
        return None
    end = series[-1]
    span = end["day"] - start["day"]
    if span <= 0:
        return None
    return round((end["front_position"] - start["front_position"]) / span, 6)


def summarize(series, profile, dx, h, n_sub):
    return {
        "timeseries": series,
        "final_profile": [round(x, 6) for x in profile],
        "front_velocity_estimate": front_velocity(series),
        "numerics": {"sub_dt": h, "substeps_per_dt": n_sub},
    }


def main():
    ap = argparse.ArgumentParser(
        description="Logistic 增长 + 一维扩散密度场模拟（纯标准库）。"
                    "stdin 读 JSON，stdout 写 JSON。"
                    "提供 intervention 字段时输出双情景对比。",
        epilog="示例: echo '{\"n\":101,\"dx\":1,\"D\":0.5,\"r\":0.2,\"K\":1,"
               "\"days\":100,\"initial\":{\"type\":\"point\",\"position\":0,"
               "\"mass\":0.1}}' | python3 logistic_density.py")
    ap.add_argument("--indent", type=int, default=None,
                    help="输出 JSON 缩进空格数（默认紧凑输出）")
    args = ap.parse_args()

    try:
        cfg = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        json.dump({"error": "stdin 不是合法 JSON: %s" % e}, sys.stdout,
                  ensure_ascii=False)
        sys.exit(2)

    try:
        n = int(cfg.get("n", 101))
        if n < 3:
            raise ValueError("n 至少为 3")
        dx = float(cfg.get("dx", 1.0))
        D = float(cfg.get("D", 0.5))
        r = float(cfg["r"])
        K = float(cfg["K"])
        if dx <= 0 or D < 0 or K <= 0:
            raise ValueError("要求 dx>0, D>=0, K>0")
        S = as_field(cfg.get("S", 0.0), n, "S")
        L = as_field(cfg.get("L", 0.0), n, "L")
        days = float(cfg.get("days", 100))
        dt = float(cfg.get("dt", 0.1))
        if days <= 0 or dt <= 0:
            raise ValueError("days 与 dt 必须为正")
        rho0 = make_initial(cfg.get("initial", {"type": "point"}), n, dx)
    except (KeyError, ValueError, TypeError) as e:
        json.dump({"error": "参数错误: %s" % e}, sys.stdout, ensure_ascii=False)
        sys.exit(2)

    stability = {"D_dt_over_dx2_before_substep": round(D * dt / (dx * dx), 6),
                 "auto_substep": D > 0 and D * dt / (dx * dx) > 0.4,
                 "rule": "内部子步进保证 D*h/dx^2 <= 0.4"}

    params = {"n": n, "dx": dx, "D": D, "r": r, "K": K, "days": days, "dt": dt}
    series_b, prof_b, h, n_sub = run(list(rho0), D, r, K, S, L, dx, dt, days)
    base = {"params": params, "stability": stability,
            **summarize(series_b, prof_b, dx, h, n_sub)}

    iv = cfg.get("intervention")
    if not iv:
        json.dump(base, sys.stdout, ensure_ascii=False, indent=args.indent)
        sys.stdout.write("\n")
        return

    start_day = float(iv.get("start_day", 0))
    ov = iv.get("overrides", {})
    D2 = float(ov.get("D", D)); r2 = float(ov.get("r", r))
    K2 = float(ov.get("K", K))
    S2 = as_field(ov.get("S", cfg.get("S", 0.0)), n, "intervention.S")
    L2 = as_field(ov.get("L", cfg.get("L", 0.0)), n, "intervention.L")
    if K2 <= 0 or D2 < 0:
        json.dump({"error": "intervention.overrides 要求 D>=0, K>0"},
                  sys.stdout, ensure_ascii=False)
        sys.exit(2)

    if start_day <= 0:
        series_i, prof_i, h2, ns2 = run(list(rho0), D2, r2, K2, S2, L2,
                                        dx, dt, days)
    else:
        pre_days = min(start_day, days)
        series_pre, prof_pre, _, _ = run(list(rho0), D, r, K, S, L,
                                         dx, dt, pre_days)
        series_post, prof_i, h2, ns2 = run(list(prof_pre), D2, r2, K2, S2, L2,
                                           dx, dt, days - pre_days)
        series_i = series_pre[:-1] + [
            {**p, "day": round(p["day"] + pre_days, 4)} for p in series_post]
    iv_out = {"params": {**params, "intervention_start_day": start_day,
                         "overrides": {"D": D2, "r": r2, "K": K2}},
              **summarize(series_i, prof_i, dx, h2, ns2)}
    effect = {
        "final_total_mass_delta":
            round(series_i[-1]["total_mass"] - series_b[-1]["total_mass"], 6),
        "final_front_delta":
            series_i[-1]["front_position"] - series_b[-1]["front_position"],
        "final_max_density_delta":
            round(series_i[-1]["max_density"] - series_b[-1]["max_density"], 6),
        "note": "差值=干预效果量化；负值表示干预降低了密度/减缓了扩张",
    }
    out = {"baseline": base, "intervention": iv_out, "effect": effect}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=args.indent)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
