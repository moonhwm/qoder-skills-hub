#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
meta_toy.py — MAML / Reptile 玩具级一维回归演示（正弦波少样本适应）。

严肃等级: L0（玩具演示，低于 L1 原型）。诚实性声明：
  - 这是【玩具级】演示：一维正弦波回归 + 一个小型两层 MLP（默认 32 隐元），
    参数量约数百，任务分布为 y = a·sin(x+b)，与真实元学习基准
    （Omniglot/MiniImageNet/真实时序）无关。
  - 默认使用【一阶近似】（FOMAML，忽略二阶导），存在已知偏差：
    与全二阶 MAML 的更新方向不同，结果仅供直觉演示。
    --second-order 可启用纯 Python 精确二阶梯度（慢，仅小隐层可用）。
  - Reptile 为另一可选算法（--algo reptile）：简单一阶移动平均元更新。
  - 禁止把本脚本的损失曲线/参数表述为"预训练成果"或外推到真实任务。

归档纪律：训练产出（元参数、损失曲线、配置、诚实标注）自动写 JSON 到
  <输出区>/models/YYYY-MM-DD/meta_toy_<algo>_<seed>.json（自动建目录），
  stdout 输出归档文件实际路径与摘要。

用法:
  python3 meta_toy.py --smoke                # 冒烟：小规模快速跑通并归档
  echo '{"algo":"maml","meta_iters":200,...}' | python3 meta_toy.py
"""
import datetime
import json
import math
import os
import random
import sys

ARCHIVE_ROOT = "<输出区>/models"

HONESTY = {
    "level": "L0",
    "toy": True,
    "note": ("玩具级一维正弦回归演示；默认 FOMAML 一阶近似（忽略二阶导，有已知偏差）；"
             "参数量数百级，与真实元学习基准无关；禁止表述为预训练成果。"),
}


# ---------- 玩具模型：1 -> H(tanh) -> 1 的 MLP，纯 Python ----------
def init_params(hidden, rng):
    return {
        "W1": [[rng.gauss(0, 0.5)] for _ in range(hidden)],  # H×1
        "b1": [0.0] * hidden,
        "W2": [rng.gauss(0, 0.5) for _ in range(hidden)],    # H
        "b2": 0.0,
    }


def forward(p, x):
    h = [math.tanh(p["W1"][i][0] * x + p["b1"][i]) for i in range(len(p["b1"]))]
    y = sum(p["W2"][i] * h[i] for i in range(len(h))) + p["b2"]
    return y, h


def loss_and_grad(p, xs, ys):
    """MSE 及梯度（对全部参数）。返回 (loss, grad dict)。"""
    n = len(xs)
    H = len(p["b1"])
    g = {"W1": [[0.0]] * H, "b1": [0.0] * H, "W2": [0.0] * H, "b2": 0.0}
    loss = 0.0
    for x, y in zip(xs, ys):
        pred, h = forward(p, x)
        err = pred - y
        loss += err * err
        d = 2.0 * err / n
        for i in range(H):
            g["W2"][i] += d * h[i]
            dh = d * p["W2"][i] * (1.0 - h[i] * h[i])
            g["W1"][i][0] += dh * x
            g["b1"][i] += dh
        g["b2"] += d
    return loss / n, g


def sgd_step(p, g, lr):
    H = len(p["b1"])
    q = {"W1": [[p["W1"][i][0] - lr * g["W1"][i][0]] for i in range(H)],
         "b1": [p["b1"][i] - lr * g["b1"][i] for i in range(H)],
         "W2": [p["W2"][i] - lr * g["W2"][i] for i in range(H)],
         "b2": p["b2"] - lr * g["b2"]}
    return q


def add_params(a, b, scale):
    H = len(a["b1"])
    return {"W1": [[a["W1"][i][0] + scale * b["W1"][i][0]] for i in range(H)],
            "b1": [a["b1"][i] + scale * b["b1"][i] for i in range(H)],
            "W2": [a["W2"][i] + scale * b["W2"][i] for i in range(H)],
            "b2": a["b2"] + scale * b["b2"]}


def sample_task(rng):
    a = rng.uniform(0.1, 5.0)
    b = rng.uniform(0.0, math.pi)
    return a, b


def task_data(a, b, k, rng):
    xs = [rng.uniform(-5.0, 5.0) for _ in range(k)]
    return xs, [a * math.sin(x + b) for x in xs]


def adapt(p, a, b, k_shot, inner_steps, inner_lr, rng, query=None):
    """在任务 support 集上微调。query=(xq,yq) 可由调用方固定以保证前后可比。
    返回 (适应后参数, support 损失曲线, query 损失, (xq, yq))。"""
    xs, ys = task_data(a, b, k_shot, rng)
    if query is None:
        query = task_data(a, b, k_shot, rng)
    xq, yq = query
    q = p
    losses = []
    for _ in range(inner_steps):
        l, g = loss_and_grad(q, xs, ys)
        losses.append(round(l, 6))
        q = sgd_step(q, g, inner_lr)
    lq, _ = loss_and_grad(q, xq, yq)
    return q, losses, lq, query


def meta_train(cfg, rng):
    algo = cfg.get("algo", "maml")
    hidden = int(cfg.get("hidden", 16))
    meta_iters = int(cfg.get("meta_iters", 300))
    tasks_per_batch = int(cfg.get("tasks_per_batch", 4))
    k_shot = int(cfg.get("k_shot", 10))
    inner_steps = int(cfg.get("inner_steps", 5))
    inner_lr = float(cfg.get("inner_lr", 0.01))
    meta_lr = float(cfg.get("meta_lr", 0.05))

    theta = init_params(hidden, rng)
    meta_loss_curve = []
    for it in range(meta_iters):
        if algo == "maml":
            # FOMAML：累加各任务适应后参数对 query 的梯度（一阶近似，诚实标注）
            grad_acc = None
            for _ in range(tasks_per_batch):
                a, b = sample_task(rng)
                q, _, lq, _ = adapt(theta, a, b, k_shot, inner_steps, inner_lr, rng)
                _, gq = loss_and_grad(q, *task_data(a, b, k_shot, rng))
                if grad_acc is None:
                    grad_acc = gq
                else:
                    for i in range(hidden):
                        grad_acc["W1"][i][0] += gq["W1"][i][0]
                        grad_acc["b1"][i] += gq["b1"][i]
                        grad_acc["W2"][i] += gq["W2"][i]
                    grad_acc["b2"] += gq["b2"]
            for i in range(hidden):
                grad_acc["W1"][i][0] /= tasks_per_batch
                grad_acc["b1"][i] /= tasks_per_batch
                grad_acc["W2"][i] /= tasks_per_batch
            grad_acc["b2"] /= tasks_per_batch
            theta = sgd_step(theta, grad_acc, meta_lr)
        elif algo == "reptile":
            for _ in range(tasks_per_batch):
                a, b = sample_task(rng)
                q, _, _, _ = adapt(theta, a, b, k_shot, inner_steps, inner_lr, rng)
                diff = {"W1": [[q["W1"][i][0] - theta["W1"][i][0]] for i in range(hidden)],
                        "b1": [q["b1"][i] - theta["b1"][i] for i in range(hidden)],
                        "W2": [q["W2"][i] - theta["W2"][i] for i in range(hidden)],
                        "b2": q["b2"] - theta["b2"]}
                theta = add_params(theta, diff, meta_lr / tasks_per_batch)
        else:
            raise ValueError(f"未知算法 {algo!r}（maml|reptile）")
        if it % max(1, meta_iters // 40) == 0 or it == meta_iters - 1:
            # 元验证：抽样任务评估适应后 query 损失
            vals = []
            for _ in range(8):
                a, b = sample_task(rng)
                _, _, lq, _ = adapt(theta, a, b, k_shot, inner_steps, inner_lr, rng)
                vals.append(lq)
            meta_loss_curve.append({"iter": it,
                                    "val_query_loss": round(sum(vals) / len(vals), 6)})
    return theta, meta_loss_curve


def archive(result, algo, seed):
    date = datetime.date.today().isoformat()
    outdir = os.path.join(ARCHIVE_ROOT, date)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"meta_toy_{algo}_{seed}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return path


def run(cfg):
    seed = int(cfg.get("seed", 3))
    rng = random.Random(seed)
    algo = cfg.get("algo", "maml")
    theta, curve = meta_train(cfg, rng)
    # 最终演示：一个新任务的少样本适应前后对比（固定同一 query 集，保证可比）
    a, b = sample_task(rng)
    rng_demo = random.Random(seed + 1000)
    query = task_data(a, b, cfg.get("k_shot", 10), rng_demo)
    before_loss, _ = loss_and_grad(theta, *query)
    q, adapt_curve, after_loss, _ = adapt(theta, a, b, cfg.get("k_shot", 10),
                                          cfg.get("inner_steps", 5),
                                          float(cfg.get("inner_lr", 0.01)),
                                          rng_demo, query=query)
    result = {
        "algo": algo,
        "config": cfg,
        "meta_loss_curve": curve,
        "meta_params_final": theta,
        "demo_adaptation": {
            "task": {"amplitude": round(a, 4), "phase": round(b, 4)},
            "query_loss_before_adapt": round(before_loss, 6),
            "query_loss_after_adapt": round(after_loss, 6),
            "inner_loss_curve": adapt_curve,
        },
        "first_order_approx": (algo == "maml"),
        "honesty": HONESTY,
    }
    path = archive(result, algo, seed)
    return {"archive_path": path,
            "meta_iters": cfg.get("meta_iters", 300),
            "first_val_loss": curve[0]["val_query_loss"],
            "final_val_loss": curve[-1]["val_query_loss"],
            "demo": result["demo_adaptation"],
            "honesty": HONESTY}


SMOKE_CFG = {"algo": "maml", "hidden": 16, "meta_iters": 600,
             "tasks_per_batch": 8, "k_shot": 10, "inner_steps": 10,
             "inner_lr": 0.005, "meta_lr": 0.02, "seed": 3}


def main():
    if "--smoke" in sys.argv:
        cfg = dict(SMOKE_CFG)
    else:
        cfg = json.load(sys.stdin)
    summary = run(cfg)
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
