# -*- coding: utf-8 -*-
"""pre_push_gate.py —— 推送前闸（应令条⑤：「引入 MFA、Git、Hook…」＋令条⑥「Git 钩子校验未通过时自动触发回滚」）
★"回滚"之实现：闸不过 ⇒ 推送不发生（本地不变、远端不动）—— 这是最安全之回滚。
检查项（任一项不过即拒推）：
  ①台账链自洽（cairn：cairn_ledger verify）
  ②镜像树签名（mirror：node tools/sha3-tree.mjs verify）
  ③署名抽验（本仓中被本次提交改动之 *CAIRN-*.otl，过 sig_verify；若有"不符"即拒）
  ④大件闸（禁 >5 MB 入库）
  ⑤机密模式闸（禁 AK/SK 形态串入库）
用法：python pre_push_gate.py [--repo <路径>] [--selftest]
（中文串一律用「」）
"""
import argparse, pathlib, re, subprocess, sys

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
SECRET = re.compile(r"(LTAI[0-9A-Za-z]{12,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})")
BIG = 5 * 1024 * 1024


def sh(args, cwd=None, to=180):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=to)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def changed(repo):
    rc, out = sh(["git", "-C", str(repo), "diff", "--name-only", "HEAD~1", "HEAD"], to=60)
    return [l.strip() for l in out.splitlines() if l.strip()] if rc == 0 else []


def gate(repo, selftest=False):
    repo = pathlib.Path(repo); name = repo.name
    print("  ═══ 推送前闸 ｜ 仓 %s ═══" % name)
    fails = []
    # ① 台账链（cairn）
    if (repo/"ledger"/"cairn_ledger.py").exists() or "cairn" == name:
        rc, out = sh([sys.executable, str(SEAT/"ledger"/"cairn_ledger.py"), "verify"], to=180)
        ok = "PASS" in out
        print("   ① 台账链自洽 ⇒ %s" % ("✓" if ok else "✗ " + out.strip().splitlines()[-1][:70]))
        if not ok: fails.append("台账链")
    # ② 镜像树签名（mirror）
    if (repo/"tools"/"sha3-tree.mjs").exists():
        rc, out = sh(["node", str(repo/"tools"/"sha3-tree.mjs"), "verify"], cwd=str(repo), to=300)
        up = out.upper()
        ok = rc == 0 and ("VERIFIED" in up or "OK" in up or "MATCH" in up or "一致" in out or "成功" in out)
        print("   ② 镜像树签名 ⇒ %s" % ("✓" if ok else "✗ " + out.strip().splitlines()[-1][:70]))
        if not ok: fails.append("镜像树签名")
    # ③ 署名抽验（改动之 CAIRN 件）
    ch = [c for c in changed(repo) if "CAIRN-" in c and c.endswith(".otl")]
    if ch:
        bad = 0
        for c in ch[:20]:
            p = repo/c
            if not p.exists(): continue
            rc, out = sh([sys.executable, str(SEAT/"exp"/"sig_verify.py"), "--paths", str(p)], to=120)
            if "不符" in out and "不符 0" not in out: bad += 1
        print("   ③ 署名抽验 ⇒ 改动件 %d，不符 %d ⇒ %s" % (len(ch), bad, "✓" if bad == 0 else "✗"))
        if bad: fails.append("署名不符")
    # ④ 大件闸
    big = []
    for r in ("notes", "tools", "deliverables", "mem"):
        d = repo/r
        if d.exists():
            for p in d.rglob("*"):
                try:
                    if p.is_file() and p.stat().st_size > BIG: big.append(str(p.relative_to(repo)))
                except Exception: pass
    print("   ④ 大件闸（>5 MB）⇒ %s" % ("✓ 无" if not big else "✗ " + "、".join(big[:3])))
    if big: fails.append("大件 %d 个" % len(big))
    # ⑤ 机密模式闸
    hits, notes = [], []
    for r in ("notes", "tools", "skills"):
        d = repo/r
        if d.exists():
            for p in list(d.rglob("*.md"))[:200] + list(d.rglob("*.py"))[:200]:
                try:
                    t = p.read_text(encoding="utf-8", errors="replace")
                except Exception: continue
                m = SECRET.search(t)
                if not m: continue
                rel = str(p.relative_to(repo))
                if re.search(r"(^|[\\/])(test|tests|sample|samples|example|examples|fixture|fixtures|mock|mocks)", rel, re.I):
                    notes.append("%s（测试夹具，已忽略）" % rel); continue
                v = m.group(1)
                if re.fullmatch(r"(?i)(abcdefghijklmnopqrstuvwxyz.*|1234567890.*|sk-abc.*)", v) or len(set(v)) <= 4:
                    notes.append("%s（疑似占位／顺序串，已忽略）" % rel); continue
                hits.append("%s（%s…%s）" % (rel, v[:6], v[-4:]))
    print("   ⑤ 机密模式闸 ⇒ %s%s" % ("✓ 无" if not hits else "✗ " + "；".join(hits[:3]),
          ("（另忽略 %d 处测试夹具／占位串）" % len(notes)) if notes else ""))
    for nt in notes[:3]: print("        · 已忽略：" + nt)
    if hits: fails.append("机密模式 %d 处" % len(hits))
    import os as _os
    if selftest or _os.environ.get("OPL_GATE_SELFTEST") == "1":
        print("   ★ 自检：注入一个人为失败项（--selftest 或 OPL_GATE_SELFTEST=1）")
        fails.append("自检注入项")
    if fails:
        print("   ✗ 闸未过 ⇒ ★拒绝推送（回滚＝推送不发生；本地与远端皆不变）｜未过项：%s" % "、".join(fails))
        return 1
    print("   ✓ 五项皆过 ⇒ 放行推送")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(gate(a.repo, a.selftest))
