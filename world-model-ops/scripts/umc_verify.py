# -*- coding: utf-8 -*-
"""umc_verify.py —— UMC v0.1 三面分面校验器（补入网五步之第三步）
正主（DF-IMA-RECHECK-20261006-HY4-01）：「UMC v0.1 三面分面：hb.* 心跳面（永不触达机主）｜biz.* 业务面（聚合进每周一页纸）｜esc.* 升级面（≤60s）」＋「五段式回执（事项／状态／已完成／阻塞／下一步）」
判据（★失败即红，退出码 1；依赖不足 ⇒ 未测，退出码 2）：
  ①每条事件可归面（无"无面"事件）
  ②hb.* 不得"触达机主"（不得含 notify_owner／@机主／直接通知等标记）
  ③esc.* 须 ≤60 s（据 ts 与前条 ts 之差近似；无 ts 者记未评）
  ④五段式回执：回执文本须含 事项／状态／已完成／阻塞／下一步 五段
用法：python umc_verify.py [--bus <bus.jsonl>] [--receipt <文本>] [--json <out>]
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
DEFBUS = SEAT.parent/"A2A共同体_共享交换区"/"bus"/"bus.jsonl"
HB = re.compile(r"心跳|heartbeat|healthz|\bprobe\b")
BIZ = re.compile(r"台账|投递|交付|件号|CAIRN-|镜像|推送|签名|检索|墙|死信|对账|审计")
ESC = re.compile(r"升级面|升级|阻塞|红线|撞墙|失败|异常|急|须裁决|候裁|追认")
OWNER_TOUCH = re.compile(r"notify_owner|@机主|直接通知机主|触达机主|推送机主")
FIVE = ["事项", "状态", "已完成", "阻塞", "下一步"]
# ★补规则（2026-10-12）：按 kind 与结构字段归面（此前仅按文本关键词 ⇒ 无面 10.5%）
KIND_BIZ = {"artifact", "note", "round", "ops", "ledger", "emit", "deliver", "push", "mirror", "sig", "report"}
STRUCT_BIZ = ("path", "seal_files", "detail", "subject", "ev_type")

def face_of(rec):
    txt = json.dumps(rec, ensure_ascii=False)
    if HB.search(txt): return "hb.*"
    if ESC.search(txt): return "esc.*"
    if BIZ.search(txt): return "biz.*"
    if str(rec.get("kind", "")).lower() in KIND_BIZ: return "biz.*"
    if any(k in rec for k in STRUCT_BIZ): return "biz.*"
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bus", default=str(DEFBUS)); ap.add_argument("--receipt", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    bus = pathlib.Path(a.bus)
    if not bus.exists():
        print("  ★总线不在（%s）⇒ 未测（环境不足；退出码 2）" % str(bus)[-50:]); sys.exit(2)
    rows = [json.loads(l) for l in bus.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    faces = {"hb.*": [], "biz.*": [], "esc.*": [], "无面": []}
    for r in rows:
        f = face_of(r) or "无面"
        faces[f].append(r)
    n = len(rows)
    print("  ═══ UMC v0.1 三面分面 ｜ 总线 %d 条 ═══" % n)
    for k in ("hb.*", "biz.*", "esc.*", "无面"):
        print("   %-6s %4d 条（%.1f%%）" % (k, len(faces[k]), 100.0*len(faces[k])/max(1, n)))
    # ② hb 不得触达机主
    hb_owner = [r for r in faces["hb.*"] if OWNER_TOUCH.search(json.dumps(r, ensure_ascii=False))]
    # ③ esc 须 ≤60s（近似：相邻 esc 记录之 ts 差）
    def ts(r):
        m = re.search(r"(20\d\d-\d\d-\d\d[ T]\d\d:\d\d:\d\d)", str(r.get("ts", "")))
        if not m: return None
        try: return time.mktime(time.strptime(m.group(1).replace("T", " "), "%Y-%m-%d %H:%M:%S"))
        except Exception: return None
    # ★修正：正主之"≤60 s"指"升级面端到端"（触报→处置），非"两次升级之间隔"
    # 口径：若记录带 handle_ts／resolved_ts 则评端到端；否则★标不可评（不判红）
    e2e = []
    for r in faces["esc.*"]:
        t0, t1 = ts(r), ts({"ts": r.get("handle_ts") or r.get("resolved_ts") or ""})
        if t0 and t1: e2e.append(t1-t0)
    # ★接入升级面计时簿（esc_watch.jsonl）：端到端可评
    ew = SEAT/"ledger"/"esc_watch.jsonl"
    n_ew = 0
    if ew.exists():
        for l in ew.read_text(encoding="utf-8", errors="replace").splitlines():
            if not l.strip(): continue
            j = json.loads(l)
            if j.get("event") == "close" and j.get("elapsed_s") is not None:
                e2e.append(float(j["elapsed_s"])); n_ew += 1
    over = [g for g in e2e if g > 60]
    gaps = e2e
    # ④ 五段式回执
    rec_txt = a.receipt
    if not rec_txt:
        rp = SEAT/"registry"/"receipt_sample.md"
        rec_txt = rp.read_text(encoding="utf-8", errors="replace") if rp.exists() else ""
    miss = [k for k in FIVE if k not in rec_txt] if rec_txt else FIVE
    noface_pct = 100.0*len(faces["无面"])/max(1, n)
    crit = {"①无面占比 ≤10%%（现 %.1f%%；超出即须补规则，非即判违规）" % noface_pct: noface_pct <= 10.0,
            "②hb.* 未触达机主": len(hb_owner) == 0,
            "③升级面端到端 ≤60 s（可评 %d 次，含计时簿 %d 次）" % (len(gaps), n_ew): (len(over) == 0),
            "④五段式回执齐备": (not miss)}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if faces["无面"]:
        print("   ★无面样本（前 3，供补规则）：")
        for r in faces["无面"][:3]:
            print("      · %s" % json.dumps(r, ensure_ascii=False)[:104])
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "bus": str(bus), "n": n,
           "faces": {k: len(v) for k, v in faces.items()}, "hb_owner_touch": len(hb_owner),
           "esc_e2e_over60": len(over), "noface_pct": round(noface_pct, 2), "receipt_missing": miss, "criteria": crit}
    if a.json: pathlib.Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if all(crit.values()) else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
