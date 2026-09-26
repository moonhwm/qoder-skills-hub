#!/usr/bin/env python3
"""playground_log.py —— 项目工作区甲轮次留痕追加器（纯标准库）

用法：
  python3 playground_log.py <游乐场目录> --round N --gain "一句新知" [--tokens 估算] [--artifacts f1,f2]
  python3 playground_log.py --self-test   # 离线冒烟
留痕文件：<目录>/<轮次日志>，每轮一行 JSON。
"""
import argparse, json, os, sys, time


def append_round(playdir: str, round_n: int, gain: str, tokens: int, artifacts: list) -> dict:
    os.makedirs(playdir, exist_ok=True)
    ev = {"round": round_n, "gain": gain, "tokens_est": tokens,
          "artifacts": artifacts, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    path = os.path.join(playdir, "<轮次日志>")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def self_test() -> int:
    d = "/tmp/playground_selftest"
    if os.path.exists(os.path.join(d, "<轮次日志>")):
        os.remove(os.path.join(d, "<轮次日志>"))
    append_round(d, 1, "测试新知", 100, ["a.md"])
    append_round(d, 2, "第二条", 200, [])
    lines = open(os.path.join(d, "<轮次日志>"), encoding="utf-8").read().strip().split("\n")
    ok = len(lines) == 2 and json.loads(lines[0])["gain"] == "测试新知"
    print(f"self_test: lines={len(lines)} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    ap = argparse.ArgumentParser()
    ap.add_argument("playdir")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--gain", required=True)
    ap.add_argument("--tokens", type=int, default=0)
    ap.add_argument("--artifacts", default="")
    a = ap.parse_args()
    ev = append_round(a.playdir, a.round, a.gain, a.tokens,
                      [x for x in a.artifacts.split(",") if x])
    print(json.dumps(ev, ensure_ascii=False))
