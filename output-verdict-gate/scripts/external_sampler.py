#!/usr/bin/env python3
"""external_sampler.py — 10 抽 1 外部席抽样送审器（v0.3.2）

制度落地：常态全自动 → 10 抽 1 送外部席（外部模型甲-V4-Pro + GLM-5.2 双席）→ 疑难案才请人类席。

用法：
  python3 external_sampler.py draw --case-id <案号> [--rate 0.1] [--seed 固定种子]
      只抽签不送审。输出 HIT/MISS + 随机数，留痕可复核（同案号同种子结果一致）。
  python3 external_sampler.py run --case-id <案号> --task <任务书.md> [--rate 0.1]
      抽签；HIT 则依次送 deepseek-v4-pro 与 glm-5.2，回执落盘 --outdir（默认 <输出区>/外部席回执/）。
      MISS 则只登记抽样日志，零调用零费用。
  python3 external_sampler.py --self-test
      离线自检：100 次抽签命中率应在 10%±9%（二项 99% 区间）内；固定种子可复现。

设计约束：
- 凭证只读 <用户配置目录>/external_seat.json（api_key 永不落任何输出）。
- 抽样随机数源：sha256(case_id + seed) 前 8 字节 → [0,1)。确定性、可审计、防「重抽到过」。
- 抽样日志：--outdir/sampling_ledger.jsonl，每行 {case_id, rate, draw, hit, seats_called, ts}。
- 费用闸门：单次 run 最多 2 席 × 1 案；rate 上限 0.5（防止误设成全送）。
"""
import argparse, hashlib, json, os, sys, datetime, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("external_seat", os.path.join(HERE, "external_seat.py"))
es = importlib.util.module_from_spec(spec); spec.loader.exec_module(es)

# 四外部席（v0.4.0 扩席，用户授权）：外部模型甲/GLM/Qwen/openPangu 四个不同训练谱系。
# 注：池内 kimi-平台版本甲 与内部评审同源，不作外部席（去相关价值为零）；deepseek-v4-flash 留作廉价预筛备选。
SEATS = ["deepseek-v4-pro", "glm-5.2", "qwen3-32b", "openpangu-2.0-pro"]
RATE_CAP = 1.0  # v0.4.0 用户授权可至 1 抽 1；>0.5 须抽样日志注明授权来源

def draw(case_id: str, rate: float, seed: str) -> tuple[float, bool]:
    """确定性抽签：同案号同种子结果可复现（防重抽）。"""
    if not (0 < rate <= RATE_CAP):
        raise ValueError(f"rate 须在 (0, {RATE_CAP}]，当前 {rate}")
    h = hashlib.sha256(f"{case_id}|{seed}".encode()).digest()
    x = int.from_bytes(h[:8], "big") / 2**64
    return x, x < rate

def log_line(outdir: str, rec: dict):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "sampling_ledger.jsonl"), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def cmd_draw(a):
    x, hit = draw(a.case_id, a.rate, a.seed)
    print(f"{'HIT' if hit else 'MISS'} draw={x:.4f} rate={a.rate} case={a.case_id}")
    return 0 if hit else 1

def cmd_run(a):
    x, hit = draw(a.case_id, a.rate, a.seed)
    rec = {"case_id": a.case_id, "rate": a.rate, "draw": round(x, 6),
           "hit": hit, "seats_called": [], "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    if a.rate > 0.5:
        rec["auth"] = "rate>0.5 用户显式授权（2026-08-30「可以逐渐增加席位和复核频率到1抽1」）"
    if not hit:
        rec["note"] = "MISS，零调用"
        log_line(a.outdir, rec)
        print(f"MISS draw={x:.4f} — 本案不送外部席，已登记。")
        return 1
    conf = es.load_conf()
    task = open(a.task, encoding="utf-8").read()
    for seat in SEATS:
        try:
            ans = es.chat({**conf, "model": seat}, task)
            md5 = hashlib.md5(ans.encode()).hexdigest()[:16]
            out = os.path.join(a.outdir, f"外部席回执_{a.case_id}_{seat}.md")
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"# 外部席回执（{seat}）\n\n- 案号: {a.case_id}\n- 时间: {rec['ts']}\n"
                        f"- md5[:16]: {md5}\n- 任务书: {a.task}\n- 抽样: draw={x:.4f} rate={a.rate}\n\n"
                        f"## 回答原文\n\n{ans}\n")
            rec["seats_called"].append({"seat": seat, "md5": md5, "receipt": out})
            print(f"  {seat}: 回执落盘 {out} md5={md5}")
        except Exception as e:
            rec["seats_called"].append({"seat": seat, "error": str(e)[:200]})
            print(f"  {seat}: 调用失败 {e}", file=sys.stderr)
    log_line(a.outdir, rec)
    return 0

def self_test():
    hits = sum(draw(f"case-{i}", 0.1, "selftest")[1] for i in range(100))
    ok_rate = 1 <= hits <= 19  # 二项(n=100,p=0.1) 近似 99% 区间
    r1 = draw("案A", 0.1, "s"); r2 = draw("案A", 0.1, "s")
    ok_repro = r1 == r2
    print(f"100抽命中 {hits} 次（期望≈10）{'OK' if ok_rate else 'FAIL'}；"
          f"同案复现 {'OK' if ok_repro else 'FAIL'}")
    return 0 if (ok_rate and ok_repro) else 2

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="10抽1外部席抽样送审器")
    p.add_argument("--self-test", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    for name in ("draw", "run"):
        s = sub.add_parser(name)
        s.add_argument("--case-id", required=True)
        s.add_argument("--rate", type=float, default=0.1)
        s.add_argument("--seed", default="verdict-gate-v1")
        s.add_argument("--outdir", default="<输出区>/外部席回执")
        if name == "run":
            s.add_argument("--task", required=True)
    a = p.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.cmd == "draw":
        sys.exit(cmd_draw(a))
    if a.cmd == "run":
        sys.exit(cmd_run(a))
    p.print_help()
