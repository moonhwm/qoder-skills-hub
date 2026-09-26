#!/usr/bin/env python3
"""furnace_runner.py — 外池压测/燃烧炉体模板（线程安全版）

血泪教训（2026-09-01/02 实证）：跨轮不 join 的工作线程指数堆积——31,944 根线程
拖死全机（Cannot fork / pthread_create）。本模板的铁律：每轮结束 join 排水，
线程数归零才进下一轮。

用法：
  1) 实现 worker(task, pool) -> dict 结果（内部自行调用外部 API，凭据走环境变量）；
  2) 配 POOLS 信号量与 DEADLINE；
  3) python3 furnace_runner.py  （自带 --self-test 离线冒烟，不触网）
台账：JSONL 逐窑记录（ev/ts/pool/task/tokens/cost），凭据零落盘。
"""
import json
import os
import threading
import time
from queue import Queue

# ---- 配置区（按池实测调整） ------------------------------------------------
POOLS = {"default": 4}          # 池名 -> 并发信号量上限（实证调参：air 8 / 4.6v 6 / general 2 量级起步）
DEADLINE = None                 # epoch 秒；礼品池死线转 epoch 填入，到期停排新窑
LEDGER = "furnace_ledger.jsonl" # 台账路径
SEMS = {name: threading.Semaphore(n) for name, n in POOLS.items()}
_lock = threading.Lock()


def log_ev(ev: dict) -> None:
    ev.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    line = json.dumps(ev, ensure_ascii=False)
    with _lock:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def worker(task: dict, pool: str) -> dict:
    """真实炉里在此调外部 API。self-test 时按 task 返回伪结果。"""
    time.sleep(0.01)
    return {"tokens": task.get("est_tokens", 0), "cost": 0, "ok": True}


def run_round(tasks: list[dict], pool: str = "default") -> list[dict]:
    """跑一轮：信号量限流 + 逐窑落账 + 全线程 join 排水（铁律）。"""
    q = Queue()
    for t in tasks:
        q.put(t)
    results: list[dict] = []
    threads: list[threading.Thread] = []

    def _one():
        while True:
            try:
                task = q.get_nowait()
            except Exception:
                return
            if DEADLINE and time.time() > DEADLINE:
                log_ev({"ev": "deadline_skip", "id": task.get("id"), "pool": pool})
                q.task_done()
                continue
            with SEMS[pool]:
                try:
                    r = worker(task, pool)
                except Exception as e:  # 单窑失败不炸炉：落账继续
                    r = {"ok": False, "error": type(e).__name__}
                log_ev({"ev": "done", "id": task.get("id"), "pool": pool, **r})
                results.append({"task": task, **r})
            q.task_done()

    n = min(len(tasks), POOLS[pool] * 2)
    for _ in range(n):
        th = threading.Thread(target=_one, daemon=True)
        th.start()
        threads.append(th)
    for th in threads:  # 每轮排水：线团病防线
        th.join()
    q.join()
    return results


def self_test() -> int:
    global LEDGER
    LEDGER = "/tmp/furnace_selftest_ledger.jsonl"
    if os.path.exists(LEDGER):
        os.remove(LEDGER)
    tasks = [{"id": f"T{i:02d}", "est_tokens": 100} for i in range(20)]
    r = run_round(tasks)
    n_threads = threading.active_count()
    ok = (
        len(r) == 20
        and all(x.get("ok") for x in r)
        and sum(1 for _ in open(LEDGER, encoding="utf-8")) == 20
        and n_threads <= 2  # 排水核验：主线程外无残留
    )
    print(f"self_test: done={len(r)}/20 ledger=20 residual_threads={n_threads} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    print("模板件：复制本文件，实现 worker() 后调用 run_round(tasks, pool)。离线核验：--self-test")
