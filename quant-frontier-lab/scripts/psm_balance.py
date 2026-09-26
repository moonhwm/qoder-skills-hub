#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
psm_balance.py — 倾向得分匹配（PSM）院校公平对比工具。

严肃等级: L1（教学级原型）。诚实性声明：
  - PSM 只能平衡【已观测】混淆变量；任何未观测混淆都会导致估计偏误。
  - 【硬提示】混淆变量清单必须人工确认：哪些协变量应进入倾向得分模型，
    属于领域判断，本脚本无法替你决定。输出中强制附该提示。
  - logistic 回归为手写实现：numpy 可用时用 numpy.linalg 做 IRLS；
    numpy 缺失时降级为纯 Python 梯度下降（更慢、精度略低，已标注降级）。
  - 不依赖 sklearn。

输入（stdin JSON）:
{
  "covariates": ["x1", "x2", ...],            # 进入倾向得分模型的协变量名
  "rows": [{"id": "sch1", "treated": 1, "outcome": 610.5, "x1": ..., ...}, ...]
}
  treated: 1=处理组（如实验班/新教学法学校），0=对照组。

输出（stdout JSON）:
  - propensity_scores（每校倾向得分与 logit）
  - matches（卡钳内最近邻，卡钳 = 0.2 × SD(logit)，处理组无放回可选）
  - smd_table（匹配前后各协变量标准化均差 SMD 对照；|SMD|<0.1 视为平衡）
  - att_estimate（匹配后处理组平均处理效应的朴素估计，附强烈警示）
  - hard_notice（混淆变量人工确认硬提示）+ honesty 等级标注

冒烟：python3 psm_balance.py --smoke   （30 校合成数据）
"""
import json
import math
import sys

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:  # 降级：纯 Python 梯度下降
    np = None
    HAS_NUMPY = False

HARD_NOTICE = ("【硬提示】倾向得分模型纳入的混淆变量清单必须由领域人员人工确认；"
               "PSM 仅平衡已观测混淆，未观测混淆（如生源家庭投入、师资隐性差异）"
               "仍会造成偏误。ATT 为朴素匹配估计，非因果结论。")
HONESTY = {
    "level": "L1",
    "unverified": True,
    "note": HARD_NOTICE,
    "backend": "numpy-IRLS" if HAS_NUMPY else "pure-python-GD(degraded)",
}


def sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def fit_logistic_numpy(X, t, iters=200, ridge=1e-6):
    """IRLS（Newton-Raphson）解 logistic 回归。X: n×(p+1) 含截距列。"""
    X = np.asarray(X, dtype=float)
    t = np.asarray(t, dtype=float)
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        W = np.clip(p * (1.0 - p), 1e-9, None)
        XtW = X.T * W
        H = XtW @ X + ridge * np.eye(X.shape[1])
        g = X.T @ (t - p)
        step = np.linalg.solve(H, g)
        beta = beta + step
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return beta.tolist()


def fit_logistic_pure(X, t, iters=4000, lr=0.1):
    """纯 Python 批量梯度下降（numpy 缺失降级路径）。"""
    n, m = len(X), len(X[0])
    beta = [0.0] * m
    for _ in range(iters):
        grad = [0.0] * m
        for i in range(n):
            z = sum(beta[j] * X[i][j] for j in range(m))
            err = t[i] - sigmoid(z)
            for j in range(m):
                grad[j] += err * X[i][j]
        for j in range(m):
            beta[j] += lr * grad[j] / n
    return beta


def standardize(X):
    """每列 z-score，返回 (Z, means, sds)。"""
    m = len(X[0])
    means = [sum(row[j] for row in X) / len(X) for j in range(m)]
    sds = []
    for j in range(m):
        var = sum((row[j] - means[j]) ** 2 for row in X) / max(len(X) - 1, 1)
        sds.append(math.sqrt(var) or 1.0)
    Z = [[(row[j] - means[j]) / sds[j] for j in range(m)] for row in X]
    return Z, means, sds


def smd(x_t, x_c):
    """标准化均差：均值差 / 合并标准差。"""
    if not x_t or not x_c:
        return None
    mt = sum(x_t) / len(x_t)
    mc = sum(x_c) / len(x_c)
    vt = sum((v - mt) ** 2 for v in x_t) / max(len(x_t) - 1, 1)
    vc = sum((v - mc) ** 2 for v in x_c) / max(len(x_c) - 1, 1)
    sp = math.sqrt((vt + vc) / 2.0)
    return (mt - mc) / sp if sp > 0 else 0.0


def run(payload, with_replacement=True):
    covs = payload["covariates"]
    rows = payload["rows"]
    ids = [r["id"] for r in rows]
    t = [int(r["treated"]) for r in rows]
    y = [float(r["outcome"]) for r in rows]
    raw = [[float(r[c]) for c in covs] for r in rows]
    Z, _, _ = standardize(raw)
    X = [[1.0] + z for z in Z]  # 截距 + 标准化协变量

    if HAS_NUMPY:
        beta = fit_logistic_numpy(X, t)
    else:
        beta = fit_logistic_pure(X, t)

    ps, logit = [], []
    for i in range(len(rows)):
        z = sum(beta[j] * X[i][j] for j in range(len(beta)))
        p = min(max(sigmoid(z), 1e-9), 1 - 1e-9)
        ps.append(p)
        logit.append(math.log(p / (1 - p)))

    sd_logit = math.sqrt(sum((v - sum(logit) / len(logit)) ** 2 for v in logit)
                         / max(len(logit) - 1, 1))
    caliper = 0.2 * sd_logit

    treated_idx = [i for i in range(len(rows)) if t[i] == 1]
    control_idx = [i for i in range(len(rows)) if t[i] == 0]
    used = set()
    matches, unmatched_t = [], []
    for i in treated_idx:
        best, best_d = None, None
        for j in control_idx:
            if not with_replacement and j in used:
                continue
            d = abs(logit[i] - logit[j])
            if d <= caliper and (best_d is None or d < best_d):
                best, best_d = j, d
        if best is None:
            unmatched_t.append(ids[i])
        else:
            used.add(best)
            matches.append({"treated": ids[i], "control": ids[best],
                            "logit_dist": round(best_d, 6)})
    matched_t = [ids.index(m["treated"]) for m in matches]
    matched_c = [ids.index(m["control"]) for m in matches]

    smd_table = []
    for k, c in enumerate(covs):
        before = smd([raw[i][k] for i in treated_idx],
                     [raw[i][k] for i in control_idx])
        after = smd([raw[i][k] for i in matched_t],
                    [raw[i][k] for i in matched_c])
        smd_table.append({
            "covariate": c,
            "smd_before": round(before, 4) if before is not None else None,
            "smd_after": round(after, 4) if after is not None else None,
            "balanced_after": (after is not None and abs(after) < 0.1),
        })

    att = None
    if matches:
        att = sum(y[i] - y[j] for i, j in zip(matched_t, matched_c)) / len(matches)

    return {
        "backend": HONESTY["backend"],
        "n": len(rows), "n_treated": len(treated_idx), "n_control": len(control_idx),
        "caliper": round(caliper, 6),
        "with_replacement": with_replacement,
        "propensity_scores": [{"id": ids[i], "ps": round(ps[i], 6),
                               "logit": round(logit[i], 6)} for i in range(len(rows))],
        "matches": matches,
        "unmatched_treated_outside_caliper": unmatched_t,
        "smd_table": smd_table,
        "att_estimate_naive": round(att, 4) if att is not None else None,
        "hard_notice": HARD_NOTICE,
        "honesty": HONESTY,
    }


def make_smoke(n=30, seed=42):
    import random
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        x1 = rng.gauss(0, 1)          # 生源基础
        x2 = rng.gauss(0, 1)          # 师资投入
        # 处理分配与 x1 正相关（制造观测混淆）
        p = 1.0 / (1.0 + math.exp(-(x1 + 0.3 * x2 - 0.2)))
        tr = 1 if rng.random() < p else 0
        outcome = 600 + 8 * tr + 20 * x1 + 5 * x2 + rng.gauss(0, 3)
        rows.append({"id": f"sch{i+1:02d}", "treated": tr,
                     "outcome": round(outcome, 2),
                     "x1": round(x1, 4), "x2": round(x2, 4)})
    return {"covariates": ["x1", "x2"], "rows": rows}


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
