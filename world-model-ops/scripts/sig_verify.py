# -*- coding: utf-8 -*-
"""sig_verify.py —— 署名可复验器（★独立于 sig_block.py，不改原工具）
口径（照 sig_block.py v5 之声明）：
  正文 SHA3-512 树根（单文件叶即根）= sha3_512( norm(raw[:raw.find(b"\\n<!-- SIG-BLOCK")]) )
  norm: latin1 往返 ＋ CRLF→LF
用法：python sig_verify.py --paths <file1> <file2> …   ｜ --dir <dir> --glob "<pat>"
输出：逐件 相符／不符／无署名块；并给总计
（中文串一律用「」）
"""
import argparse, glob, hashlib, pathlib, re, sys

SENT = b"\n<!-- SIG-BLOCK"
DIG = re.compile(r"本件正文 SHA3-512 树根（署名块之前）\*\* \| `([0-9a-f]{128})`")


def norm(b: bytes) -> bytes:
    return b.decode("latin1").replace("\r\n", "\n").encode("latin1")


def root_of_1(b: bytes) -> str:
    return hashlib.sha3_512(norm(b)).hexdigest()


def check(p: pathlib.Path):
    raw = p.read_bytes()
    i = raw.find(SENT)
    if i < 0:
        return "nosig", None, None
    recorded = None
    m = DIG.search(raw.decode("utf-8", "replace"))
    if m:
        recorded = m.group(1)
    calc = root_of_1(raw[:i])
    if recorded is None:
        return "nodig", calc, None
    return ("ok" if recorded == calc else "mismatch"), calc, recorded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=[])
    ap.add_argument("--dir", default="")
    ap.add_argument("--glob", default="*.otl")
    a = ap.parse_args()
    files = [pathlib.Path(x) for x in a.paths]
    if a.dir:
        files += [pathlib.Path(x) for x in sorted(glob.glob(str(pathlib.Path(a.dir) / a.glob)))]
    if not files:
        print("  无输入"); return
    stat = {"ok": 0, "mismatch": 0, "nosig": 0, "nodig": 0}
    bad = []
    for f in files:
        st, calc, rec = check(f)
        stat[st] += 1
        if st != "ok":
            bad.append((f.name, st))
            print("   ★ %-58s ⇒ %s" % (f.name[:58], {"mismatch": "不符（内容与记录不符）", "nosig": "无署名块", "nodig": "无树根记录"}[st]))
    tot = len(files)
    print("  ═══ 复验 %d 件 ═══" % tot)
    print("   ★ 相符 %d ｜ 不符 %d ｜ 无署名块 %d ｜ 无树根记录 %d" % (stat["ok"], stat["mismatch"], stat["nosig"], stat["nodig"]))
    print("   ⇒ 判：%s" % ("★全部相符（署名可复算）" if stat["ok"] == tot else "★有例外，见上列"))
    if bad[:5]:
        print("   例外样例：" + "；".join("%s(%s)" % (n, s) for n, s in bad[:5]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
