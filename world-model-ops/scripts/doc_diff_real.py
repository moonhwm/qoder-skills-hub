# -*- coding: utf-8 -*-
"""doc_diff_real.py —— 文档版本"真实差异"判定（★先去 URL 再比）
为何需要：WPS 导出之图片 URL 带签名，每次复拉长度漂移 ⇒ 直接比字数会把"URL 抖动"误报为"内容改动"。
用法：
  python doc_diff_real.py --name <文档名> [--a <旧版本> --b <新版本>]   # 单件
  python doc_diff_real.py --sweep                                     # 全档扫最近两版
输出：差异行数／仅 URL 差异行数／真实内容差异行（列前几处）／净字数差
（中文串一律用「」）
"""
import argparse, difflib, json, pathlib, re, sys

HOME = pathlib.Path.home()
D = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"/"archive"/"docs"
URL = re.compile(r"https?://[^\s)\]]+")


def deurl(s):
    return URL.sub("URL", s)


def cmp(name, a=None, b=None):
    d = D/name
    vs = sorted(d.glob("v_2026*.md"))
    if len(vs) < 2: return None
    pa, pb = (d/a, d/b) if (a and b) else (vs[-2], vs[-1])
    if not (pa.exists() and pb.exists()): return None
    ta = pa.read_text(encoding="utf-8", errors="replace").splitlines()
    tb = pb.read_text(encoding="utf-8", errors="replace").splitlines()
    m = min(len(ta), len(tb))
    diff = [i for i in range(m) if ta[i] != tb[i]]
    onlyurl = [i for i in diff if deurl(ta[i]) == deurl(tb[i])]
    real = [i for i in diff if deurl(ta[i]) != deurl(tb[i])]
    ch = (len("".join(tb)) - len("".join(ta)))
    ch_nourl = (len("".join(deurl(x) for x in tb)) - len("".join(deurl(x) for x in ta)))
    return {"doc": name, "a": pa.stem[2:], "b": pb.stem[2:], "lines": [len(ta), len(tb)],
            "diff_lines": len(diff), "url_only_lines": len(onlyurl), "real_lines": len(real),
            "char_delta": ch, "char_delta_nourl": ch_nourl, "real_samples": [ta[i][:90] for i in real[:3]]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--name", default="")
    ap.add_argument("--a", default=""); ap.add_argument("--b", default=""); ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    names = sorted([p.name for p in D.iterdir() if p.is_dir()]) if args.sweep else [args.name]
    rows = []
    for n in names:
        r = cmp(n, args.a or None, args.b or None)
        if not r: continue
        rows.append(r)
        flag = "★真实改动" if r["real_lines"] else "（仅URL抖动）"
        print("   %-16s %s⇒%s ｜ 差异行 %3d（仅URL %3d／真实 %3d）｜ 净字 %+d（去URL后 %+d）｜ %s" % (
            r["doc"][:16], r["a"][-4:], r["b"][-4:], r["diff_lines"], r["url_only_lines"], r["real_lines"],
            r["char_delta"], r["char_delta_nourl"], flag))
        for s in r["real_samples"]: print("        · " + s)
    if rows:
        real = [r for r in rows if r["real_lines"]]
        print("   ⇒ 判：共 %d 件；★真实内容改动 %d 件%s" % (len(rows), len(real),
              ("：" + "、".join(r["doc"] for r in real)) if real else "（其余皆图片 URL 签名抖动）"))
    if args.json and rows:
        pathlib.Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
