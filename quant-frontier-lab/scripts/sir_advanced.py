#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sir_advanced.py — SIR 传染模型三算法合一对比实验台。

严肃等级: L1（教学级原型）。诚实性声明：
  ⚠ 均匀混合假设警示：Gillespie SSA 与链二项式均假设人群均匀混合
    （anyone-can-meet-anyone），真实传播存在家庭/班级/地域结构，本脚本
    的边基分区近似仅做粗粒度校正。结果不可直接用于真实疫情决策。

三种算法：
  1. gillespie  —— 精确随机模拟（Gillespie SSA，事件驱动，连续时间）。
  2. chain_binomial —— 链二项式离散时间模型（每步感染数 ~ Binomial(S, 1-(1-p)^I)）。
  3. edge_partition —— 边基分区近似：输入 edges 接触网络，用配置模型近似
     有效再生数 R_eff ≈ R0 × (剩余易感边占比)，按边生成树样分区传播。

输入（stdin JSON）:
{
  "N": 500, "I0": 5, "R0": 2.5, "gamma": 0.2,      # gamma=恢复率（1/天）
  "algorithms": ["gillespie", "chain_binomial", "edge_partition"],
  "t_max": 160, "seed": 7,
  "edges": [[0,1],[1,2], ...]                        # edge_partition 必需
}
R0 = beta/gamma（均匀混合下 beta = R0*gamma/N）。

输出（stdout JSON）:
  每算法：trajectory（抽样点 S/I/R）、peak（峰值感染与时间）、final_size。
  附 assumptions 警示 + honesty 等级。

冒烟：python3 sir_advanced.py --smoke   （N=500，三组算法对比，edges 为随机网络）
"""
import json
import math
import random
import sys

HONESTY = {
    "level": "L1",
    "unverified": True,
    "note": ("均匀混合假设下的教学级实现；Gillespie/链二项式不含接触结构，"
             "边基分区为配置模型近似非精确网络动力学；不可用于真实疫情决策。"),
}
WARNING = ("⚠ 均匀混合假设：真实人群存在家庭/班级/地域聚类，"
           "同质混合会高估早期传播速度、低估空间异质性影响。")


def summarize(traj):
    """traj: list of (t, S, I, R)。"""
    peak_t, peak_i = max(traj, key=lambda x: x[2])[:2]
    final_size = traj[-1][3]
    n_total = traj[0][0] + traj[0][1] + traj[0][2]
    return {"peak_infected": peak_i, "peak_time": round(peak_t, 2),
            "final_size": final_size,
            "attack_rate": round(final_size / n_total, 4)}


def gillespie(N, I0, R0, gamma, t_max, rng):
    """Gillespie SSA：两事件（感染/恢复），指数等待时间。"""
    beta = R0 * gamma / N
    S, I, R = N - I0, I0, 0
    t = 0.0
    traj = [(0.0, S, I, R)]
    record_at = 1.0
    while t < t_max and I > 0:
        a_inf = beta * S * I
        a_rec = gamma * I
        a0 = a_inf + a_rec
        if a0 <= 0:
            break
        t += rng.expovariate(a0)
        if rng.random() < a_inf / a0:
            S -= 1
            I += 1
        else:
            I -= 1
            R += 1
        while record_at <= t and record_at <= t_max:
            traj.append((record_at, S, I, R))
            record_at += 1.0
    if traj[-1][0] < t_max:
        traj.append((t_max, S, I, R))
    return traj


def chain_binomial(N, I0, R0, gamma, t_max, rng):
    """链二项式：每感染者每天以概率 p=beta 独立感染每个易感者；每天恢复概率 gamma。"""
    beta = R0 * gamma / N
    S, I, R = N - I0, I0, 0
    traj = [(0.0, S, I, R)]
    for day in range(1, int(t_max) + 1):
        if I == 0:
            traj.append((float(day), S, I, R))
            continue
        p_inf = 1.0 - (1.0 - beta) ** I  # 单个易感者当天被感染概率
        new_inf = sum(1 for _ in range(S) if rng.random() < p_inf)
        new_rec = sum(1 for _ in range(I) if rng.random() < gamma)
        S -= new_inf
        I += new_inf - new_rec
        R += new_rec
        traj.append((float(day), S, I, R))
    return traj


def edge_partition(N, I0, R0, gamma, t_max, rng, edges):
    """边基分区近似：在接触网络上用配置模型思想估计有效再生数。
    R_eff(t) ≈ R0 × (剩余"易感-未知"边数 / 总边数)，每天按 R_eff 推进分区传播。
    注：这是近似（假设网络树样局部、度分布用样本矩），非精确网络 SIR。
    """
    if not edges:
        raise ValueError("edge_partition 需要 edges 输入")
    adj = [[] for _ in range(N)]
    for u, v in edges:
        if 0 <= u < N and 0 <= v < N and u != v:
            adj[u].append(v)
            adj[v].append(u)
    deg = [len(a) for a in adj]
    m = sum(deg) // 2
    mean_d = sum(deg) / N
    mean_d2 = sum(d * d for d in deg) / N
    # 配置模型基本再生数：R0_net = (transmissibility) × (<d²>-<d>)/<d>
    kappa = (mean_d2 - mean_d) / mean_d if mean_d > 0 else 1.0
    # 校准：令均匀混合等价 R0 与网络 R0 对齐，p_trans = R0 / kappa（截断到 [0,1]）
    p_trans = min(R0 / max(kappa, 1e-9), 1.0)

    state = ["S"] * N
    seeds = rng.sample(range(N), I0)
    for s in seeds:
        state[s] = "I"
    traj = []
    for day in range(0, int(t_max) + 1):
        S = state.count("S")
        I = state.count("I")
        R = state.count("R")
        traj.append((float(day), S, I, R))
        if I == 0:
            continue
        # 剩余易感边占比 → 有效再生数衰减因子（边基分区核心近似）
        si_edges = sum(1 for u in range(N) if state[u] == "S"
                       for v in adj[u] if state[v] == "I")
        s_frac = S / N
        r_eff = R0 * (si_edges / max(I * mean_d, 1)) * s_frac
        p_eff = min(p_trans * (r_eff / max(R0 * s_frac, 1e-9)), 1.0)
        new_states = state[:]
        for u in range(N):
            if state[u] != "I":
                continue
            for v in adj[u]:
                if state[v] == "S" and rng.random() < p_eff:
                    new_states[v] = "I"
            if rng.random() < gamma:
                new_states[u] = "R"
        state = new_states
    return traj, {"kappa_excess_degree": round(kappa, 4),
                  "p_trans_calibrated": round(p_trans, 4)}


def make_random_edges(N, avg_deg, rng):
    edges = set()
    while len(edges) < N * avg_deg // 2:
        u, v = rng.randrange(N), rng.randrange(N)
        if u != v:
            edges.add((min(u, v), max(u, v)))
    return sorted(edges)


def run(payload):
    N = int(payload.get("N", 500))
    I0 = int(payload.get("I0", 5))
    R0 = float(payload.get("R0", 2.5))
    gamma = float(payload.get("gamma", 0.2))
    t_max = float(payload.get("t_max", 160))
    seed = int(payload.get("seed", 7))
    algos = payload.get("algorithms",
                        ["gillespie", "chain_binomial", "edge_partition"])
    edges = payload.get("edges")
    rng = random.Random(seed)

    out = {"params": {"N": N, "I0": I0, "R0": R0, "gamma": gamma,
                      "t_max": t_max, "seed": seed},
           "warning": WARNING, "algorithms": {}}
    if "gillespie" in algos:
        traj = gillespie(N, I0, R0, gamma, t_max, rng)
        out["algorithms"]["gillespie"] = {
            "trajectory_sampled": [[round(t, 1), s, i, r] for t, s, i, r in traj[::max(1, len(traj)//40)]],
            **summarize(traj)}
    if "chain_binomial" in algos:
        traj = chain_binomial(N, I0, R0, gamma, t_max, rng)
        out["algorithms"]["chain_binomial"] = {
            "trajectory_sampled": [[t, s, i, r] for t, s, i, r in traj[::max(1, len(traj)//40)]],
            **summarize(traj)}
    if "edge_partition" in algos:
        if edges is None:
            edges = make_random_edges(N, 6, rng)
            out["edge_note"] = "未提供 edges，使用合成随机网络（avg_deg=6）"
        traj, diag = edge_partition(N, I0, R0, gamma, t_max, rng, edges)
        out["algorithms"]["edge_partition"] = {
            "trajectory_sampled": [[t, s, i, r] for t, s, i, r in traj[::max(1, len(traj)//40)]],
            **summarize(traj), "diagnostics": diag}
    out["honesty"] = HONESTY
    return out


SMOKE = {"N": 500, "I0": 5, "R0": 2.5, "gamma": 0.2, "t_max": 160, "seed": 7,
         "algorithms": ["gillespie", "chain_binomial", "edge_partition"]}


def main():
    if "--smoke" in sys.argv:
        payload = dict(SMOKE)
        payload["edges"] = make_random_edges(500, 6, random.Random(99))
    else:
        payload = json.load(sys.stdin)
    result = run(payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
