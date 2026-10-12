# -*- coding: utf-8 -*-
"""ledger_write.py —— 台账"安全写"封装（2026-10-12 立，应 -1253 之修正）
三步一体（★防"两执行者并发覆盖"与"写后不刷快照致误报"）：
  ① 检版本：调用 ledger_gate.check ⇒ ★不一致则★中止（不写）
  ② 追加：调用 cairn_ledger.py append <条目 json>
  ③ 刷新快照：调用 ledger_gate.snapshot ⇒ 使下次 check 有正确基准
判据（可失败）：①闸检已跑；②追加已跑（或按闸中止）；③★快照已刷新（写成功时）
用法：python ledger_write.py <条目 json 相对路径（相对 ledger 目录之上一级，如 exp/led_xxx.json）>
（中文串一律用「」）
"""
import argparse, pathlib, subprocess, sys

SEAT = pathlib.Path(__file__).resolve().parent.parent
GATE = SEAT/"exp"/"ledger_gate.py"
CL = SEAT/"ledger"/"cairn_ledger.py"


def run(args, cwd=None):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("entry"); a = ap.parse_args()
    print("  ═══ 台账安全写（闸检 → 追加 → 刷新快照）═══")
    # ① 闸检
    rc, out = run([str(GATE), "check"])
    last = ((out or "").strip().splitlines() or [""])[-1]
    print("   ① 闸检 rc=%s ｜ %s" % (rc, last[:70]))
    if rc != 0:
        print("   ⇒ ★闸报不一致 ⇒ ★中止（不写）—— ★宁停不超")
        return 2
    # ② 追加
    rc2, out2 = run([str(CL), "append", a.entry], cwd=str(SEAT))
    line2 = [l for l in (out2 or "").splitlines() if "已追加" in l or "ERR" in l or "REFUSE" in l]
    print("   ② 追加 rc=%s ｜ %s" % (rc2, (line2[0].strip() if line2 else (out2 or "").strip()[-70:])))
    if rc2 != 0 or not line2:
        print("   ⇒ ★追加未成 ⇒ 不刷新快照（免掩盖）")
        return 1
    # ③ 刷新快照
    rc3, out3 = run([str(GATE), "snapshot"])
    print("   ③ 刷快照 rc=%s ｜ %s" % (rc3, ((out3 or "").strip().splitlines() or [""])[-1][:70]))
    crit = {"①闸检已跑": True, "②追加已跑": rc2 == 0, "③★快照已刷新": rc3 == 0}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    print("   ⇒ 判：★三步齐备（闸检一致 → 追加成功 → 快照已刷新）")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
