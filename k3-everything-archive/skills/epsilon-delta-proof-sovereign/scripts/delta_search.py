#!/usr/bin/env python3
"""delta_search.py — ε-δ 数值侦察器(计算启发,非证明)

对命题 lim_{x→c} f(x) = L 做数值侦察:
- 给定 eps,在 (0, max_delta] 上二分搜索最大可用 δ(采样验证 |f(x)-L|<eps)
- 报告候选 δ 与疑似反例;输出 JSON 轨迹
红线:本脚本输出是数值证据,不是证明(SKILL.md §5)。
用法:
  python3 delta_search.py --f "x**2" --c 2 --L 4 --eps 0.1
  python3 delta_search.py --f "1/x" --c 1 --L 1 --eps 0.01 --samples 2000
依赖: 仅标准库+math(免numpy,沙盒安全)。
"""
import argparse, json, math, random, time

def make_f(expr):
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed["abs"] = abs
    code = compile(expr, "<f>", "eval")
    def f(x):
        return eval(code, {"__builtins__": {}}, {**allowed, "x": x})
    return f

def holds(f, c, L, eps, delta, samples, seed):
    rng = random.Random(seed)
    worst = 0.0
    counter = None
    for _ in range(samples):
        # 0<|x-c|<delta 采样(避开 c 点)
        r = rng.random() * delta
        x = c + r if rng.random() < 0.5 else c - r
        try:
            dev = abs(f(x) - L)
        except Exception:
            counter = {"x": x, "err": "f undefined"}; return False, worst, counter
        if dev > worst: worst = dev
        if dev >= eps:
            counter = {"x": x, "dev": dev}
            return False, worst, counter
    return True, worst, counter

def search(f, c, L, eps, max_delta=1.0, samples=1500, seed=42):
    ok, worst, _ = holds(f, c, L, eps, max_delta, samples, seed)
    if not ok:
        lo, hi = 0.0, max_delta
    else:
        # 放大找失败界
        lo, hi = max_delta, max_delta * 4
        for _ in range(30):
            ok, _, _ = holds(f, c, L, eps, hi, samples, seed)
            if not ok: break
            lo, hi = hi, hi * 2
        else:
            return {"delta": lo, "note": "侦察范围上限内全成立", "worst": None}
    for _ in range(40):
        mid = (lo + hi) / 2
        ok, _, _ = holds(f, c, L, eps, mid, samples, seed)
        if ok: lo = mid
        else: hi = mid
    ok, worst, counter = holds(f, c, L, eps, hi, samples * 2, seed + 1)
    return {"delta": lo, "worst_dev_at_delta": worst,
            "counterexample_above": counter, "note": "数值侦察,非证明"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--f", required=True); ap.add_argument("--c", type=float, required=True)
    ap.add_argument("--L", type=float, required=True); ap.add_argument("--eps", type=float, required=True)
    ap.add_argument("--max-delta", type=float, default=1.0)
    ap.add_argument("--samples", type=int, default=1500)
    a = ap.parse_args()
    f = make_f(a.f)
    t0 = time.time()
    res = search(f, a.c, a.L, a.eps, a.max_delta, a.samples)
    out = {"proposition": f"lim_(x->{a.c}) ({a.f}) = {a.L}", "eps": a.eps,
           "data_cutoff": time.strftime("%Y-%m-%d"), "elapsed_s": round(time.time() - t0, 2),
           "verdict": "numeric_scouting_only", **res}
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
