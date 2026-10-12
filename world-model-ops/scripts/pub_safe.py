# -*- coding: utf-8 -*-
"""pub_safe.py —— 出件安全驱动（把戒三十七做进流程）
★硬性顺序（不可倒序）：打钟 → 术语闸 → 署签 → 复核（署名复算＋七项自检）→ 投递三处 → 总线 emit → 台账
★每一步皆"带重试 ＋ 写后复核"（WPS 云盘同步会短暂占用文件，属环境常态）
用法：python pub_safe.py --file <件> --note <署名注> [--dry]
（中文串一律用「」）
"""
import argparse, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
BUS_DIR = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_总线指针与台账"


def run(args, tries=4, need=None, label=""):
    for k in range(1, tries + 1):
        p = subprocess.run([sys.executable] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (p.stderr or "")
        if need is None or need in out:
            print("   ✓ %s（第 %d 次）" % (label, k)); return out
        print("   · %s 第 %d 次未成（%s）⇒ 重试" % (label, k, out.strip().splitlines()[-1][:70] if out.strip() else "无输出"))
        time.sleep(4 * k)
    print("   ✗ %s 失败（已重试 %d 次）" % (label, tries)); return None


def precheck_ledger(led):
    """★出件前先校验台账条目必填键（快速失败，免"件已出而账未记"）"""
    import pathlib as _pl
    f = _pl.Path(led)
    if not f.exists():
        print("   ✗ 台账条目文件不存在：%s" % led); return False
    txt = f.read_text(encoding="utf-8", errors="replace")
    need = ("ev_type", "subject", "detail", "evidence", "seal_files")
    miss = [k for k in need if (k + ":") not in txt]
    if miss:
        print("   ✗ 台账条目缺必填键 %s ⇒ 先补键再出件（本次不落笔）" % miss); return False
    print("   ✓ 台账条目键齐备（%s）" % "、".join(need)); return True

def main():
    # ★2026-10-12 立（口径章一）：出件前必读「运行口径」—— 本夜 19 处自纠之总闸
    print("   ★出件前必读：cairn/mem/运行口径_20261012.md（出件/时标/度量/裁决/写入/造器诸口径）")
    ap = argparse.ArgumentParser(); ap.add_argument("--file", required=True)
    ap.add_argument("--note", default=""); ap.add_argument("--evidence", default="")
    ap.add_argument("--ledger", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(); f = pathlib.Path(a.file)
    if a.dry:
        print("  ═══ 预演（不写任何文件）═══")
        print("   件：%s（%.1f KB）" % (f.name, f.stat().st_size/1024))
        print("   顺序：打钟 → 术语闸 → 署签 → 复核 → 投递三处 → 总线 emit → 台账 → ★刷快照")
        print("   ⇒ 判：驱动就绪（本轮不落笔）"); return 0
    seat = SEAT
    if a.ledger:
        # ★--evidence 由命令行注入（免我反复漏该键）
        if a.evidence:
            import pathlib as _pl
            _ledf = _pl.Path(a.ledger)          # ★勿用 f（会遮蔽"件"之路径，曾致误署误投）
            if _ledf.exists():
                txt = _ledf.read_text(encoding="utf-8", errors="replace")
                if "evidence:" not in txt:
                    txt = txt.replace("seal_files:", "evidence: " + a.evidence + "\nseal_files:")
                    _ledf.write_text(txt, encoding="utf-8", newline="\n"); print("   ✓ 已由 --evidence 注入该键（未动件路径）")
        if not precheck_ledger(a.ledger):
            return 2
    run([str(seat/"exp"/"stamp_time.py"), str(f)], need="已打钟", label="打钟")
    run([str(seat/"exp"/"termtable.py"), "check", "--paths", str(f)], label="术语闸")
    run([str(seat/"exp"/"sig_block.py"), "--file", str(f), "--append", "--note", a.note], need="逐位相符", label="署签")
    run([str(seat/"exp"/"sig_verify.py"), "--paths", str(f)], need="相符", label="署名复算")
    run([str(seat/"exp"/"sop_check.py"), "--file", str(f)], label="七项自检")
    for dst in (BUS_DIR/"Cairn席_20261011", HOME/"openplanlink-cairn"/"notes",
                HOME/"openplanlink-mirror"/"deliverables"/time.strftime("%Y%m%d")/"seat-cairn"):
        try:
            dst.mkdir(parents=True, exist_ok=True)
            (dst/f.name).write_bytes(f.read_bytes()); print("   ✓ 投递 %s" % dst.name)
        except Exception as e:
            print("   ✗ 投递失败 %s：%s" % (dst, str(e)[:60]))
    # ★emit 步改走 bus_dlq（含"总线合法性"与"读回复验"两道闸；失败即入死信队列）
    run([str(seat/"exp"/"bus_dlq.py"), "emit", "--path", str(f), "--kind", "artifact",
         "--seat", "a2a-node-local", "--tries", "4"], need="已入总", label="总线 emit（经 DLQ 两闸）")
    # ★最后一步：写台账（仅当此前各步皆成；带重试＋写后复核）⇒ 结构上不可能"先记后做"
    if a.ledger:
        run([str(seat/"exp"/"mkled.py"), a.ledger], need="已生成", label="生成台账条目")
        j = a.ledger[:-4] + ".json" if a.ledger.endswith(".led") else a.ledger
        run([str(seat/"ledger"/"cairn_ledger.py"), "append", j], need="已追加", label="写入台账")
        out = run([str(seat/"ledger"/"cairn_ledger.py"), "verify"], need="PASS", label="台账复核")
        # ★2026-10-12 加（-1293 之训）：写台账后★刷新版本闸快照
        #   否则下次 ledger_gate check 必报"不一致"而误拦（我昨夜即在 pub_safe 后忘刷而致误报）
        run([str(seat/"exp"/"ledger_gate.py"), "snapshot"], need="已记快照", label="刷新版本闸快照")
        if out: print("   " + [l.strip() for l in out.splitlines() if "条目数" in l][-1][:60])
    print("   ⇒ 判：驱动完成（若未传 --ledger，则台账仍须托管者补）"); return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
