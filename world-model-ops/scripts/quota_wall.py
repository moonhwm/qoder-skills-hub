#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""quota_wall.py —— 撞墙即停（额度墙检测 + 零重试 + 通道切换）。

依《跨生态建设方案》第七章（四）：遇到额度墙（墙码 1308/1310/1005）零重试，
按预案切换通道或等待窗口，异常事件按「撞墙即停」原则处置并全程留痕。
纯标准库，Windows 直跑。
"""

WALL_CODES = {1308, 1310, 1005}      # 额度墙错误码
RETRYABLE = {429, 500, 502, 503}     # 可重试错误码


def is_wall(code):
    return code in WALL_CODES


def policy(code):
    """返回处置策略：撞墙即停（零重试）或按退避重试。"""
    if is_wall(code):
        return {"action": "stop", "retry": 0,
                "note": "撞墙即停：切换通道或等待窗口，全程留痕"}
    if code in RETRYABLE:
        return {"action": "retry", "retry": 3, "backoff": "exponential",
                "note": "可重试：指数退避上限 3"}
    return {"action": "stop", "retry": 0, "note": "未知错误：停止待人工"}


class WallLedger:
    """撞墙留痕：append-only 记录撞墙事件，供审计对账。"""

    def __init__(self, path):
        self.path = path

    def record(self, code, context=""):
        import json
        import datetime
        rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
               "code": code, "wall": is_wall(code), "context": context,
               "policy": policy(code)["action"]}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec


if __name__ == "__main__":
    print("  墙码 =", WALL_CODES)
    print("  policy(1308) =", policy(1308))
    print("  policy(429)  =", policy(429))
    print("  policy(999)  =", policy(999))
    import tempfile
    wl = WallLedger(tempfile.gettempdir() + "\\wall_ledger_demo.jsonl")
    print("  撞墙留痕 =", wl.record(1308, "demo"))
