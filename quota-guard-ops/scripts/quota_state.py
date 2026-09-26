#!/usr/bin/env python3
# quota_state.py v1.0.0 — 额度状态台账与分档判定（Q0–Q3）
# 用法:
#   python3 quota_state.py show                     # 查看当前档位与台账
#   python3 quota_state.py set <Q0|Q1|Q2|Q3> <理由>  # 信号到档（人工/主程序驱动）
#   python3 quota_state.py signal <quota_error|pack_prompt|ok>  # 信号输入自动判档
# 台账: <注册处>/额度状态台账.json
import json, sys, os
from datetime import datetime, timezone, timedelta

LEDGER = "<注册处>/额度状态台账.json"
TIERS = ["Q0", "Q1", "Q2", "Q3"]
TIER_RULES = {
    "Q0": "绿灯·充裕：全栈常态（Swarm 可用），遥测照常",
    "Q1": "黄灯·关注：单线程优先，子代理 ≤2，非必要不派多席",
    "Q2": "橙灯·紧张：骨架先行，禁派子代理；加油包消耗须用户知情同意（单独一句明示）",
    "Q3": "红灯·止损：quota 止损条款——停推新任务，成果落盘，交接等重置或用户拍板",
}
SIGNAL_MAP = {
    "quota_error": "Q3",   # 工具/子代理返回 quota exhausted 类错误
    "pack_prompt": "Q2",   # 出现加油包提示（计费窗口开启信号）
    "ok": "Q0",            # 信号复位（经用户确认或新周期开始）
}

def load():
    if os.path.exists(LEDGER):
        try:
            return json.load(open(LEDGER, encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[WARN] 台账损坏（{e}），按默认 Q0 重建并备份损坏件")
            try: os.replace(LEDGER, LEDGER + ".corrupt.bak")
            except OSError: pass
    return {"version": "1.0.0", "tier": "Q0", "history": [], "note": "额度状态台账（「额度守护件」）"}

def save(s):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(s, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    cmd = sys.argv[1]
    s = load()
    if cmd == "show":
        print(f"当前档位: {s['tier']} — {TIER_RULES[s['tier']]}")
        for h in s["history"][-5:]:
            print(f"  {h['ts']}  {h['from']}→{h['to']}  {h['reason']}")
        return 0
    if cmd == "set" and len(sys.argv) >= 4:
        new, reason = sys.argv[2], " ".join(sys.argv[3:])
    elif cmd == "signal" and len(sys.argv) >= 3:
        sig = sys.argv[2]
        if sig not in SIGNAL_MAP:
            print(f"[FAIL] 未知信号 {sig}，可选: {list(SIGNAL_MAP)}"); return 2
        new, reason = SIGNAL_MAP[sig], f"signal={sig}"
        # 信号只升不降（降档须 set 显式确认，防误复位）
        if TIERS.index(new) < TIERS.index(s["tier"]):
            print(f"[保持] 信号 {sig} 指向 {new}，低于当前 {s['tier']}，降档须 set 显式确认")
            return 0
    else:
        print(__doc__); return 2
    if new not in TIERS:
        print(f"[FAIL] 档位须为 {TIERS}"); return 2
    s["history"].append({"ts": now(), "from": s["tier"], "to": new, "reason": reason})
    s["tier"] = new
    save(s)
    print(f"[OK] 档位变更 → {new} — {TIER_RULES[new]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
