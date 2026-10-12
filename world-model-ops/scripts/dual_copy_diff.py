# -*- coding: utf-8 -*-
"""dual_copy_diff.py —— 双副本同步性核（2026-10-13 立，应 -1321 之发现）
动机：-1321 见 cairn/tools 与 seat/exp 有同名器而内容不一（如 glb_anim_verify／url_audit）⇒ 不知规模。
本器（★零外呼；流式 64 KB 读，低内存）：
  ① 取两目录之 *.py 名集 ⇒ 交／左独有／右独有；② 对交集逐支算 sha3(16)（流式）⇒ 判同／异；
  ③ 报统计与异者前 20（★并按"两版之字节数差"排序，差异大者在前）
判据（可失败）：①两目录皆可读；②交集 ≥1；③★同／异之数已给
用法：python dual_copy_diff.py --a <dirA> --b <dirB> [--json out]
（中文串一律用「」）
"""
import argparse, hashlib, json, pathlib, sys, time


def sha3_16(p, chunk=65536):
    h = hashlib.sha3_256()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--json", default=""); a = ap.parse_args()
    A, B = pathlib.Path(a.a), pathlib.Path(a.b)
    print("  ═══ 双副本同步性核（★流式 sha3，低内存）═══")
    if not (A.is_dir() and B.is_dir()):
        print("   ★目录不在（A=%s ｜ B=%s）" % (A.is_dir(), B.is_dir())); return 2
    na = {p.stem: p for p in A.glob("*.py")}
    nb = {p.stem: p for p in B.glob("*.py")}
    inter = sorted(set(na) & set(nb))
    onlyA = sorted(set(na) - set(nb)); onlyB = sorted(set(nb) - set(na))
    print("   A=%s（%d 支）｜ B=%s（%d 支）｜ ★交集 %d ｜ A 独有 %d ｜ B 独有 %d"
          % (A.name, len(na), B.name, len(nb), len(inter), len(onlyA), len(onlyB)))
    same = []; diff = []
    for n in inter:
        try:
            ha, hb = sha3_16(na[n]), sha3_16(nb[n])
            sa, sb = na[n].stat().st_size, nb[n].stat().st_size
        except Exception:
            continue
        (same if ha == hb else diff).append({"name": n, "ba": sa, "bb": sb, "d": sb-sa})
    diff.sort(key=lambda r: -abs(r["d"]))
    print("   ★同 %d ｜ ★异 %d（★占交集 %.1f%%）" % (len(same), len(diff), 100*len(diff)/max(1, len(inter))))
    print("   ── 异者前 20（按字节差绝对值排序）──")
    for r in diff[:20]:
        print("      ★%-30s ｜ A %7d B ｜ B %7d B ｜ Δ %+d" % (r["name"][:30], r["ba"], r["bb"], r["d"]))
    if onlyB[:8]:
        print("   ★B 独有前 8：%s" % "、".join(onlyB[:8]))
    if onlyA[:8]:
        print("   ★A 独有前 8：%s" % "、".join(onlyA[:8]))
    crit = {"①两目录皆可读": True, "②交集 ≥1": len(inter) >= 1, "③★同／异之数已给": True}
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "a": A.name, "b": B.name, "na": len(na), "nb": len(nb), "inter": len(inter),
            "same": len(same), "diff": diff, "only_a": onlyA, "only_b": onlyB, "criteria": crit},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
