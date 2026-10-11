# -*- coding: utf-8 -*-
"""sop_check.py —— 交付完整度核验器（一件一键核七步 SOP 之落地痕）
核五项：
  ① 时点行（stamp_time 之「时点：北京时间 …」且在件内）
  ② 署名（SIG-BLOCK 在场 ＋ 树根逐字复算相符，借 sig_verify 之口径）
  ③ 总线（bus.jsonl 内有该件名之 emit 记录）
  ④ 正本仓 notes/ 有同名件
  ⑤ 镜像落点（deliverables/<日期>/seat-cairn）有同名件
用法：python sop_check.py --file <件> [--bus <总线目录>]
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys

HOME = pathlib.Path.home()
CAIRN = HOME/"openplanlink-cairn"
MIRROR = HOME/"openplanlink-mirror"
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
DEFAULT_BUS = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"/"bus"
STAMP = re.compile(r"时点：北京时间\s*\**\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})")
DATE = re.compile(r"(2026\d{4})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--bus", default=str(DEFAULT_BUS))
    a = ap.parse_args()
    p = pathlib.Path(a.file)
    txt = p.read_text(encoding="utf-8", errors="replace")
    res = {}

    m = STAMP.search(txt)
    res["① 时点行"] = ("✓ " + m.group(1) + " " + m.group(2)) if m else "✗ 缺（须 stamp_time.py）"

    sys.path.insert(0, str(SEAT/"exp"))
    try:
        import sig_verify as SV
        st, calc, rec = SV.check(p)
        res["② 署名复算"] = {"ok": "✓ 相符（%s…）" % calc[:16], "mismatch": "✗ 不符",
                          "nosig": "✗ 无署名块", "nodig": "✗ 无树根记录"}[st]
    except Exception as e:
        res["② 署名复算"] = "⚠ 未能核：%s" % str(e)[:60]

    busf = pathlib.Path(a.bus)/"bus.jsonl"
    hit = None
    if busf.exists():
        for line in busf.read_text(encoding="utf-8", errors="replace").splitlines():
            if p.name in line:
                try:
                    j = json.loads(line)
                    hit = "seq=%s id=%s" % (j.get("seq"), str(j.get("id"))[:8])
                except Exception:
                    hit = "有记录"
                break
    res["③ 总线 emit"] = ("✓ " + hit) if hit else "✗ bus.jsonl 内未见该件名"

    res["④ 正本仓 notes/"] = "✓ 在" if (CAIRN/"notes"/p.name).exists() else "✗ 不在"

    md = DATE.search(p.name)
    mir = MIRROR/"deliverables"/(md.group(1) if md else "")/"seat-cairn"/p.name
    res["⑤ 镜像落点"] = ("✓ " + str(mir.parent.relative_to(MIRROR))) if mir.exists() else "✗ 不在"

    print("  ═══ 交付完整度：%s ═══" % p.name[:70])
    ok = 0
    for k, v in res.items():
        print("   %-14s %s" % (k, v))
        if str(v).startswith("✓"): ok += 1

    # ⑥ 仓推送实测（★「已推」只能来自测量，不得手写）
    import subprocess
    print("   ⑥ 仓推送实测（ls-remote）")
    for name, rp in (("cairn", CAIRN), ("mirror", MIRROR),
                     ("hub", HOME/"qoder-skills-hub"),
                     ("k3", HOME/"sleepless-flower-under-sealevel")):
        try:
            lo = subprocess.run(["git", "-C", str(rp), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=30).stdout.strip()
            rm = subprocess.run(["git", "-C", str(rp), "ls-remote", "origin", "main"],
                                capture_output=True, text=True, timeout=60).stdout.strip()
            rs = rm.split()[0] if rm else ""
            if not rs:
                st = "origin 不可达 ⇒ 待补推"
            elif rs == lo:
                st = "✓ 一致（%s）" % lo[:12]
            else:
                st = "★待补推 local=%s origin=%s" % (lo[:12], rs[:12])
        except Exception as e:
            st = "⚠ 未能核：%s" % str(e)[:50]
        print("      %-7s %s" % (name, st))

    print("   ⇒ 判：%d／5 项落地%s" % (ok, "" if ok == 5 else "  ★有缺项，须补"))
    return 0 if ok == 5 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
