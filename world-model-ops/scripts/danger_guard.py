# -*- coding: utf-8 -*-
"""danger_guard.py —— 危险命令闸（★借 letta-code `hooks/block-rm-rf.sh` 之思路，2026-10-12）
用途：①--check "<命令>" 单条自查（命中即拒，退出码 1，并留痕）②--selftest 自测（危险者须全被拦、安全者须全通过）
     ③--file <脚本> 扫一个脚本/文本中之危险形态
★边界（如实）：本器不是 shell hook —— 它拦不住"已经跑出"的命令，只能作为"我事前自查之器"（须自觉调用）；
   真正的兜底仍在 pre_push_gate（推送前闸）与"删除前须核绝对路径"之纪律。
（中文串一律用「」）
"""
import argparse, json, pathlib, re, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
LED = SEAT/"ledger"/"danger_ledger.jsonl"

# ★危险形态（正则 → 说明）
RULES = [
    (r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|f[a-zA-Z]*r)\b", "rm -rf（递归强删）"),
    (r"Remove-Item[^\n|]*-Recurse[^\n|]*-Force", "Remove-Item -Recurse -Force（递归强删）"),
    (r"\bdel\s+/[fsq]\b", "del /f /s /q（批量删）"),
    (r"\bformat\s+[a-zA-Z]:", "format 盘符（格式化）"),
    (r"git\s+push[^\n]*--force(?!-with-lease)", "git push --force（未带 lease）"),
    (r"git\s+reset\s+--hard", "git reset --hard（弃改）"),
    (r"git\s+clean\s+-[a-zA-Z]*[fdx]", "git clean -fdx（清未跟踪）"),
    # ★自纠（2026-10-12）：原"通配符删除"规则过宽（rm 后任意处有 * 即判险）⇒ 扫本席 60 脚本误报 3 处
    #   （如 `rm_up_%s" % side, *prism(` 及我自写之正则文本）⇒ 收紧为"路径样之通配且与 rm／del 同命令"
    (r"(?:rm|Remove-Item|del)\s+(?:-[A-Za-z]+\s+)*['\"]?(?:[A-Za-z]:\\|/|\./)[^\n'\"]*\*", "路径通配删除（范围不可枚举）"),
    (r">\s*[A-Za-z]:\\[^\n]*\.(?:csv|env|key|pem)\b", "重定向覆盖凭据类文件"),
    (r"(?:A2A新席|A2A席)[^\n]*(?:rm|Remove-Item|del)\b", "对他席目录动删除"),
    (r"--force-with-lease\s*=\s*$", "--force-with-lease 空值（等同强推）"),
]

def scan(text):
    hits = []
    for pat, why in RULES:
        m = re.search(pat, text, re.I)
        if m: hits.append({"pattern": pat, "why": why, "at": m.group(0)[:60]})
    return hits

def log(rec):
    try:
        with open(LED, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", default=""); ap.add_argument("--file", default="")
    ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        DANGER = ["rm -rf C:\\Users\\欧阳宏俊\\gh-mem0",
                  "Remove-Item 'C:\\x' -Recurse -Force",
                  "git push origin main --force",
                  "del /f /s /q D:\\data\\*"]
        # ★误报样例（须放行）：本席既有脚本中之形态（原过宽规则曾误报 3 处）
        SAFE = ["banner(\"rm_up_%s\" % side); geom(*prism(sx, sy))",   # ★负例须自证安全（原先误把 rm -rf 字样写进负例）
                "RMINUS = re.compile(r\"独立复算|(?:rm|Remove-Item|del)[^\\n]*\\*\")",
                "git push gitcode main --force-with-lease=main:abc123",
                "Remove-Item 'C:\\tmp\\one.txt'",
                "python exp/pub_safe.py --file a.otl",
                "git status --short"]
        ok = True
        for c in DANGER:
            h = scan(c); good = len(h) > 0; ok &= good
            print("   危险样例 ⇒ %s ｜ %s" % ("✓ 已拦" if good else "★漏拦", c[:52]))
        for c in SAFE:
            h = scan(c); good = len(h) == 0; ok &= good
            print("   安全样例 ⇒ %s ｜ %s" % ("✓ 放行" if good else "★误拦：" + h[0]["why"], c[:52]))
        print("   ⇒ 自测判：%s" % ("✓ 全对（危险全拦、安全全放）" if ok else "★有误 ⇒ 须修规则"))
        return 0 if ok else 1
    if a.file:
        p = pathlib.Path(a.file)
        if not p.exists(): print("  ★文件不在：%s" % a.file); return 2
        text = p.read_text(encoding="utf-8", errors="replace")
        h = scan(text)
        print("  ═══ 危险形态扫描 ｜ %s ═══" % p.name)
        if not h: print("   ✓ 未命中危险形态")
        for x in h: print("   ★命中：%s ⇒ %s（%s）" % (x["why"], x["at"], x["pattern"][:40]))
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "mode": "file", "target": p.name, "hits": h})
        return 0 if not h else 1
    if a.check:
        h = scan(a.check)
        print("  ═══ 危险命令自查 ｜ %s ═══" % a.check[:70])
        if not h: print("   ✓ 未命中危险形态 ⇒ 放行")
        for x in h: print("   ★命中：%s ⇒ ★拒（%s）" % (x["why"], x["at"]))
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "mode": "check", "cmd": a.check[:200], "hits": h,
             "verdict": "拒" if h else "放行"})
        return 0 if not h else 1
    print("  用法：--check \"<命令>\" ｜ --file <脚本> ｜ --selftest")
    return 0

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
