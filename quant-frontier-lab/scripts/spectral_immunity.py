#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spectral_immunity.py — 谱半径免疫分配（谱免疫 / spectral immunization）。

严肃等级: L1（教学级原型）。诚实性声明：
  - 理论背景：传播阈值近似 τ_c ≈ 1/λ₁(A)（λ₁ 为邻接矩阵谱半径）。
    删除（免疫）节点降低剩余图的 λ₁，从而抬高传播阈值。
  - 贪心删除每步选"使剩余 λ₁ 最小"的节点：该贪心策略【非最优】，
    精确最优是 NP-hard 的组合问题；小规模可穷举对照（--exact-check）。
  - 幂迭代求 λ₁ 依赖收敛容差；非连通图按整体矩阵处理。

输入（stdin JSON）:
{
  "n": 20,
  "edges": [[0,1],[1,2], ...],   # 无向图
  "k": 5,                        # 免疫节点数
  "exact_check": false           # 可选：k 与 n 很小时穷举对照（组合数 <= 20000）
}
也接受 "adjacency": [[0/1 矩阵]]。

输出（stdout JSON）:
  - lambda1_initial / lambda1_final
  - immunization_sequence（贪心免疫节点序列，每步附删除后 λ₁）
  - lambda_curve（谱半径下降曲线）
  - exact_check（若启用：穷举最优 k 组合及 λ₁，对比贪心差距，诚实标注）
  - honesty 等级标注

冒烟：python3 spectral_immunity.py --smoke   （20 节点随机图，k=5，含穷举对照）
"""
import itertools
import json
import math
import random
import sys

HONESTY = {
    "level": "L1",
    "unverified": True,
    "note": ("贪心谱免疫非最优（精确问题 NP-hard）；幂迭代近似 λ₁；"
             "τ_c≈1/λ₁ 是淬火平均场近似，不适用于强异质/含向图的精确阈值。"),
}


def spectral_radius(adj, tol=1e-10, max_iter=10000):
    """幂迭代求对称非负矩阵最大特征值（Perron 根）。返回 (λ₁, 收敛迭代数)。"""
    n = len(adj)
    if n == 0:
        return 0.0, 0
    v = [1.0 / math.sqrt(n)] * n
    lam_old = 0.0
    for it in range(1, max_iter + 1):
        w = [sum(adj[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in w))
        if norm < 1e-15:
            return 0.0, it
        v = [x / norm for x in w]
        lam = sum(v[i] * sum(adj[i][j] * v[j] for j in range(n)) for i in range(n))
        if abs(lam - lam_old) < tol:
            return lam, it
        lam_old = lam
    return lam_old, max_iter  # 未达容差，诚实记录迭代数


def induced_submatrix(adj, removed):
    n = len(adj)
    keep = [i for i in range(n) if i not in removed]
    return [[adj[i][j] for j in keep] for i in keep]


def greedy_immunize(adj, k):
    """每步枚举候选节点，删除使剩余 λ₁ 最小者。"""
    n = len(adj)
    removed = []
    sequence = []
    lam, iters = spectral_radius(adj)
    curve = [round(lam, 6)]
    for _ in range(min(k, n)):
        best_node, best_lam = None, None
        for cand in range(n):
            if cand in removed:
                continue
            sub = induced_submatrix(adj, removed + [cand])
            lam_c, _ = spectral_radius(sub)
            if best_lam is None or lam_c < best_lam:
                best_node, best_lam = cand, lam_c
        removed.append(best_node)
        sequence.append({"node": best_node,
                         "lambda1_after": round(best_lam, 6)})
        curve.append(round(best_lam, 6))
    return sequence, curve, removed


def exact_check(adj, k, max_combos=20000):
    """小规模穷举对照：诚实量化贪心与最优的差距。"""
    n = len(adj)
    total = math.comb(n, k)
    if total > max_combos:
        return {"skipped": True,
                "reason": f"组合数 C({n},{k})={total} 超过上限 {max_combos}"}
    best_combo, best_lam = None, None
    for combo in itertools.combinations(range(n), k):
        sub = induced_submatrix(adj, list(combo))
        lam, _ = spectral_radius(sub)
        if best_lam is None or lam < best_lam:
            best_combo, best_lam = combo, lam
    return {"skipped": False, "n_combinations": total,
            "optimal_set": list(best_combo),
            "optimal_lambda1": round(best_lam, 6)}


def build_adj(payload):
    if "adjacency" in payload:
        adj = [[float(x) for x in row] for row in payload["adjacency"]]
        return adj
    n = int(payload["n"])
    adj = [[0.0] * n for _ in range(n)]
    for u, v in payload["edges"]:
        adj[u][v] = adj[v][u] = 1.0
    return adj


def run(payload):
    adj = build_adj(payload)
    k = int(payload.get("k", 1))
    lam0, iters0 = spectral_radius(adj)
    sequence, curve, removed = greedy_immunize(adj, k)
    result = {
        "n": len(adj), "k": k,
        "lambda1_initial": round(lam0, 6),
        "power_iter_converged_at": iters0,
        "immunization_sequence": sequence,
        "lambda_curve": curve,
        "lambda1_final": curve[-1],
        "honesty": HONESTY,
    }
    if payload.get("exact_check"):
        ex = exact_check(adj, k)
        result["exact_check"] = ex
        if not ex.get("skipped"):
            gap = curve[-1] - ex["optimal_lambda1"]
            result["exact_check"]["greedy_lambda1"] = curve[-1]
            result["exact_check"]["optimality_gap"] = round(gap, 6)
            result["exact_check"]["verdict"] = (
                "贪心达到最优" if abs(gap) < 1e-6
                else f"贪心次优，λ₁ 差距 {gap:.6f}（诚实标注：贪心非最优算法）")
    return result


def make_smoke(n=20, avg_deg=4, seed=11):
    rng = random.Random(seed)
    edges = set()
    # 加几个高度枢纽，模拟真实网络
    for i in range(n):
        edges.add((min(i, (i + 1) % n), max(i, (i + 1) % n)))
    while len(edges) < n * avg_deg // 2:
        u = rng.choices(range(n), weights=[(i % 5 == 0) * 9 + 1 for i in range(n)])[0]
        v = rng.randrange(n)
        if u != v:
            edges.add((min(u, v), max(u, v)))
    return {"n": n, "edges": sorted(edges), "k": 5, "exact_check": True}


def main():
    if "--smoke" in sys.argv:
        payload = make_smoke()
    else:
        payload = json.load(sys.stdin)
    result = run(payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
