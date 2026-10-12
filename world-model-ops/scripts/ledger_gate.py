# -*- coding: utf-8 -*-
"""ledger_gate.py —— 台账「版本闸」（2026-10-12 立，应 -1250 事故报之第③请求）
由来：2026-10-12 18:11:46 主台账被「重基线器」替换为 10-09 基线（786 行），而我于 18:12:27 又追加 1 条
     ⇒ ★两执行者并发写同一台账而无人察觉 ⇒ 立此闸：★写台账前先读版本，与上次记录不符则停并报。
本器（零外呼）三用：
  ① snapshot：记录当前（行数＋末条 hash）到 ledger/_version_snapshot.json
  ② check   ：比对当前与快照 ⇒ ★不符则大声报并令退出码 1（★调用者据此停手）
  ③ recover ：核「可恢复性」—— exp/led_*.json 之源档数 vs 台账行数（判能否按源档重放）
判据（可失败）：①能读到台账；②能给出（行数，末条 hash）；③★check 之结论已给（一致／不一致）
用法：python ledger_gate.py {snapshot|check|recover}
（中文串一律用「」）
"""
import argparse, hashlib, json, os, pathlib, sys, time

SEAT = pathlib.Path(__file__).resolve().parent.parent
LED = SEAT/"ledger"/"frontier_ledger.jsonl"
SNAP = SEAT/"ledger"/"_version_snapshot.json"


def state():
    if not LED.exists(): return None
    lines = [l for l in LED.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()]
    last = ""
    try: last = str(json.loads(lines[-1]).get("hash") or "")
    except Exception: pass
    return {"lines": len(lines), "last_hash": last, "size": LED.stat().st_size,
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%S+0800", time.localtime(LED.stat().st_mtime))}


def cmd_snapshot():
    s = state()
    if not s: print("   ★台账不在"); return 1
    # ★2026-10-12 自纠（-1312 之训）：改用"临时文件 ＋ os.replace"原子写
    #   因"深内存警戒 ＋ WPS 云盘锁"会使★直接写随机遭 PermissionError（Errno 13），而 os.replace 可绕开
    data = json.dumps({"snapshot_at": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), **s}, ensure_ascii=False, indent=1)
    tmp = SNAP.parent/"_snap_tmp.json"
    done = False
    for att in range(1, 4):
        try:
            tmp.write_text(data, encoding="utf-8", newline="\n")
            os.replace(str(tmp), str(SNAP))
            print("   ✓ 已记快照（★原子写，第 %d 次）：行 %d ｜ 末 hash %s ｜ mtime %s"
                  % (att, s["lines"], s["last_hash"][:16], s["mtime"]))
            done = True; break
        except Exception as ex:
            print("   · 原子写第 %d 次失败：%s" % (att, str(ex)[:60])); time.sleep(2)
    if not done:
        try:
            SNAP.write_text(data, encoding="utf-8", newline="\n")
            print("   ✓ 已记快照（★直写兜底）：行 %d" % s["lines"]); done = True
        except Exception as ex:
            print("   ✗ 两种写法皆失败：%s" % str(ex)[:70]); return 1
    return 0


def cmd_check():
    cur = state(); old = None
    if SNAP.exists():
        try: old = json.loads(SNAP.read_text(encoding="utf-8-sig"))
        except Exception: old = None
    print("  ═══ 台账版本闸 ═══")
    print("   现值：行 %d ｜ 末 hash %s ｜ mtime %s" % (cur["lines"], cur["last_hash"][:16], cur["mtime"]))
    if not old:
        print("   ★无快照 ⇒ 视为「首次」（建议先 snapshot）")
        return 0
    print("   快照：行 %d ｜ 末 hash %s ｜ %s" % (old.get("lines"), str(old.get("last_hash"))[:16], old.get("snapshot_at")))
    same = (cur["lines"] == old.get("lines")) and (cur["last_hash"] == old.get("last_hash"))
    if same:
        print("   ⇒ 判：★一致（可写）")
        return 0
    print("   ⇒ 判：★★不一致 ⇒ ★停手并报（台账已被他者改动，勿盲目追加）")
    print("      差：行 %+d ｜ 末 hash %s ⇒ %s" % (cur["lines"] - (old.get("lines") or 0),
          str(old.get("last_hash"))[:12], cur["last_hash"][:12]))
    return 1


def cmd_recover():
    src = sorted((SEAT/"exp").glob("led_*.json"))
    cur = state()
    print("  ═══ 可恢复性核查 ═══")
    print("   源档 exp/led_*.json：%d 个" % len(src))
    print("   台账现值：行 %d" % (cur["lines"] if cur else -1))
    print("   ⇒ 判：%s" % ("★源档 ≥ 台账行 ⇒ ★可按源档重放（须重算 hash 链）" if len(src) >= (cur["lines"] if cur else 0)
                          else "★源档 < 台账行 ⇒ 部分条目无源档"))
    return 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["snapshot", "check", "recover"])
    a = ap.parse_args()
    return {"snapshot": cmd_snapshot, "check": cmd_check, "recover": cmd_recover}[a.cmd]()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
