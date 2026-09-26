#!/usr/bin/env python3
"""SIRD 四室信息/疫情扩散模拟器（纯标准库，欧拉法解 ODE）。

模型方程（N = S + I + R + D 为总室容，模拟中守恒）：
    dS/dt = -beta * S * I / N
    dI/dt =  beta * S * I / N - gamma * I - delta * I
    dR/dt =  gamma * I
    dD/dt =  delta * I

语义可按场景映射：S=易感(未接触人群)、I=感染(主动传播者)、
R=恢复(不再传播/免疫)、D=消亡(流失/证伪/退出)。

输入：stdin 读取 JSON：
{
  "S0": 99000, "I0": 1000, "R0": 0, "D0": 0,
  "beta": 0.35, "gamma": 0.10, "delta": 0.01,
  "days": 120, "dt": 0.1,
  "params_conf": {"beta": "估算", "gamma": "实证", "delta": "假设"},
  "intervention": {                      // 可选；提供则进入双情景对比模式
    "start_day": 30,                     // 干预生效日
    "beta_scale": 0.6,                   // 干预后 beta 乘数（如辟谣降低传播）
    "gamma_scale": 1.5,                  // 干预后 gamma 乘数（如加速澄清/恢复）
    "delta_scale": 1.0
  }
}

输出：stdout 打印 JSON：
  单情景：{"params": {...}, "r0": ..., "timeseries": [{"day", "S", "I", "R", "D"}...],
           "peak": {"day", "I"}, "final": {...}}
  双情景：{"baseline": <单情景结果>, "intervention": <单情景结果>,
           "effect": {"peak_I_reduction", "final_R_delta",
                      "D_averted", "cumulative_I_reduction"}}
说明：本脚本只做数值模拟，不判断参数可信度；params_conf 仅原样透传到输出，
      供报告层进行置信度审查。估算参数不得在报告中标为实证级置信度。
"""

import argparse
import json
import sys

VALID_CONF = ("实证", "估算", "假设", "empirical", "estimated", "assumed")


def simulate(S0, I0, R0, D0, beta, gamma, delta, days, dt):
    """欧拉法积分 SIRD 方程，返回按日采样的时间序列、峰值与终态。"""
    N = S0 + I0 + R0 + D0
    if N <= 0:
        raise ValueError("总室容 N = S0+I0+R0+D0 必须为正")
    steps = int(round(days / dt))
    S, I, R, D = float(S0), float(I0), float(R0), float(D0)
    series = []
    peak_day, peak_I = 0.0, I
    for k in range(steps + 1):
        t = k * dt
        # 按整数日采样一次（容忍浮点误差）
        if k == 0 or abs(t - round(t)) < dt / 2.0:
            series.append({"day": round(t, 4), "S": round(S, 4), "I": round(I, 4),
                           "R": round(R, 4), "D": round(D, 4)})
        if I > peak_I:
            peak_I, peak_day = I, t
        if k == steps:
            break
        dS = -beta * S * I / N
        dI = beta * S * I / N - gamma * I - delta * I
        dR = gamma * I
        dD = delta * I
        S, I, R, D = S + dS * dt, I + dI * dt, R + dR * dt, D + dD * dt
        # 数值防护：欧拉法在 dt 过大时可能出现微小负值
        S, I, R, D = max(S, 0.0), max(I, 0.0), max(R, 0.0), max(D, 0.0)
    return {
        "timeseries": series,
        "peak": {"day": round(peak_day, 4), "I": round(peak_I, 4)},
        "final": {"S": round(S, 4), "I": round(I, 4),
                  "R": round(R, 4), "D": round(D, 4)},
        "cumulative_I": round(sum(p["I"] for p in series), 4),
    }


def validate_conf(params_conf):
    """检查置信度标注是否合法；仅校验，不修改。"""
    warnings = []
    for key, level in (params_conf or {}).items():
        if level not in VALID_CONF:
            warnings.append(
                "参数 %s 的 conf='%s' 不在合法集合 %s 内" % (key, level, VALID_CONF))
    return warnings


def main():
    ap = argparse.ArgumentParser(
        description="SIRD 四室扩散模拟（欧拉法，纯标准库）。"
                    "从 stdin 读 JSON 参数，向 stdout 写 JSON 结果。"
                    "提供 intervention 字段时输出无干预 vs 干预双情景对比。",
        epilog="示例: echo '{\"S0\":99000,\"I0\":1000,\"beta\":0.35,"
               "\"gamma\":0.1,\"delta\":0.01,\"days\":120}' | python3 sird_simulate.py")
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
        S0 = float(cfg["S0"]); I0 = float(cfg["I0"])
        R0 = float(cfg.get("R0", 0)); D0 = float(cfg.get("D0", 0))
        beta = float(cfg["beta"]); gamma = float(cfg["gamma"])
        delta = float(cfg.get("delta", 0))
        days = float(cfg.get("days", 120))
        dt = float(cfg.get("dt", 0.1))
        if dt <= 0 or days <= 0:
            raise ValueError("days 与 dt 必须为正")
    except (KeyError, ValueError, TypeError) as e:
        json.dump({"error": "参数错误: %s" % e}, sys.stdout, ensure_ascii=False)
        sys.exit(2)

    warnings = validate_conf(cfg.get("params_conf"))
    params = {"S0": S0, "I0": I0, "R0": R0, "D0": D0,
              "beta": beta, "gamma": gamma, "delta": delta,
              "days": days, "dt": dt}
    r0 = beta / (gamma + delta) if (gamma + delta) > 0 else None

    baseline = simulate(S0, I0, R0, D0, beta, gamma, delta, days, dt)
    base_out = {"params": params, "r0": r0,
                "params_conf": cfg.get("params_conf"), **baseline}

    iv = cfg.get("intervention")
    if not iv:
        out = dict(base_out)
        if warnings:
            out["conf_warnings"] = warnings
    else:
        start_day = float(iv.get("start_day", 0))
        bs = float(iv.get("beta_scale", 1.0))
        gs = float(iv.get("gamma_scale", 1.0))
        ds = float(iv.get("delta_scale", 1.0))
        # 分段模拟：start_day 前用原参数，之后用缩放参数
        if start_day <= 0:
            iv_res = simulate(S0, I0, R0, D0,
                              beta * bs, gamma * gs, delta * ds, days, dt)
        else:
            pre = simulate(S0, I0, R0, D0, beta, gamma, delta, start_day, dt)
            f = pre["final"]
            post = simulate(f["S"], f["I"], f["R"], f["D"],
                            beta * bs, gamma * gs, delta * ds,
                            days - start_day, dt)
            series = pre["timeseries"][:-1] + [
                {**p, "day": round(p["day"] + start_day, 4)}
                for p in post["timeseries"]]
            peak = max(series, key=lambda p: p["I"])
            iv_res = {
                "timeseries": series,
                "peak": {"day": peak["day"], "I": peak["I"]},
                "final": post["final"],
                "cumulative_I": round(sum(p["I"] for p in series), 4),
            }
        iv_out = {"params": {**params,
                             "beta_after": beta * bs, "gamma_after": gamma * gs,
                             "delta_after": delta * ds,
                             "intervention_start_day": start_day},
                  "r0_after": ((beta * bs) / ((gamma * gs) + (delta * ds))
                               if (gamma * gs) + (delta * ds) > 0 else None),
                  **iv_res}
        effect = {
            "peak_I_reduction": round(baseline["peak"]["I"] - iv_res["peak"]["I"], 4),
            "final_R_delta": round(iv_res["final"]["R"] - baseline["final"]["R"], 4),
            "D_averted": round(baseline["final"]["D"] - iv_res["final"]["D"], 4),
            "cumulative_I_reduction":
                round(baseline["cumulative_I"] - iv_res["cumulative_I"], 4),
            "note": "差值=干预效果量化；正值表示干预降低了传播规模/消亡数",
        }
        out = {"baseline": base_out, "intervention": iv_out, "effect": effect}
        if warnings:
            out["conf_warnings"] = warnings

    json.dump(out, sys.stdout, ensure_ascii=False, indent=args.indent)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
