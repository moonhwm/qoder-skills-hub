#!/usr/bin/env python3
"""arxiv_cite.py — 由核验过的元数据 JSONL 生成标准引文。

输入：arxiv_fetch.py 输出的 JSONL（或手写同构 JSON）。
格式：--format bibtex | gbt7714 | apa
纪律：
- 预印本引文必须带 arXiv ID 与版本号；有 journal_ref/DOI 时给出"已发表版"引文并在注记中回链 arXiv。
- 版本缺失（version_latest_seen 为 null）时引文照常生成，但 stderr 提醒"未锁版本"——
  版本漂移风险见 references/citation_standards.md 第 2 节。
- withdrawn 论文：生成引文但在注记中标 [WITHDRAWN]，并 stderr 警告——撤稿论文原则上不引，
  确需引用（如学术史讨论）必须显式声明撤稿状态。

用法：
  python3 arxiv_cite.py --format bibtex < meta.jsonl
  python3 arxiv_cite.py --format gbt7714 meta.jsonl
  python3 arxiv_cite.py --smoke
"""
import argparse
import json
import re
import sys

BIBKEY_SAFE = re.compile(r"[^a-z0-9]")


def _year(rec):
    for k in ("published", "updated"):
        v = rec.get(k)
        if v and len(v) >= 4:
            return v[:4]
    return "n.d."


def _bibkey(rec):
    fam = (rec.get("authors") or ["anon"])[0].split()[-1].lower()
    return BIBKEY_SAFE.sub("", fam) + _year(rec) + rec.get("id_base", "").replace(".", "").replace("/", "")


def to_bibtex(rec):
    key = _bibkey(rec)
    ver = rec.get("version_latest_seen") or ""
    fields = [
        ("author", " and ".join(rec.get("authors") or [])),
        ("title", "{" + (rec.get("title") or "") + "}"),
        ("year", _year(rec)),
    ]
    note_bits = []
    if rec.get("withdrawn"):
        note_bits.append("WITHDRAWN")
    if rec.get("journal_ref") or rec.get("doi"):
        # 已发表：article 形态，arXiv 回链放 note
        if rec.get("journal_ref"):
            fields.append(("journal", rec["journal_ref"]))
        if rec.get("doi"):
            fields.append(("doi", rec["doi"]))
        note_bits.append(f"Preprint: arXiv:{rec.get('id_base')}{ver}")
        entry = "article"
    else:
        fields.extend([
            ("eprint", rec.get("id_base") or ""),
            ("archivePrefix", "arXiv"),
            ("primaryClass", rec.get("primary_category") or ""),
        ])
        if ver:
            note_bits.append(f"Version {ver}")
        entry = "misc"
    if note_bits:
        fields.append(("note", "; ".join(note_bits)))
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
    return f"@{entry}{{{key},\n{body}\n}}"


# 常见中文姓氏拼音（用于"姓前名后已是原序"的启发式判定；非穷尽，拿不准仍人工核对）
COMMON_CN_SURNAMES = {
    "wang", "li", "zhang", "liu", "chen", "yang", "zhao", "huang", "zhou", "wu",
    "xu", "sun", "hu", "zhu", "gao", "lin", "he", "guo", "ma", "luo", "liang",
    "song", "zheng", "xie", "han", "tang", "feng", "yu", "dong", "xiao", "cheng",
    "cao", "yuan", "deng", "jiang", "cai", "lu", "wei", "shen", "pan", "peng",
    "lv", "su", "ren", "dai", "xia", "yan", "qin", "jin", "tao", "xue",
}


def _gbt_authors(authors):
    # GB/T 7714：姓在前全称大写，名缩写；超过 3 位用"等"（et al）
    # 启发式：首词命中常见中文姓氏 → 视为已是"姓 名"原序（如 "Li Wei" → "LI W"）；
    # 否则按西名"名 姓"处理（如 "Ashish Vaswani" → "VASWANI A"）。误判风险见
    # references/citation_standards.md 第 4 节——仍是人工核对点，只是更少触发。
    def fmt(name):
        parts = name.split()
        if len(parts) == 1:
            return parts[0].upper()
        if parts[0].lower() in COMMON_CN_SURNAMES:
            return " ".join([parts[0].upper()] + [p[0].upper() for p in parts[1:] if p])
        return " ".join([parts[-1].upper()] + [p[0].upper() for p in parts[:-1] if p])
    names = [fmt(a) for a in authors]
    if len(names) > 3:
        return ", ".join(names[:3]) + ", et al"
    return ", ".join(names)


def to_gbt7714(rec):
    """GB/T 7714-2015 顺序编码制。预印本按 [EB/OL] 电子资源处理；已发表按 [J]。"""
    au = _gbt_authors(rec.get("authors") or [])
    title = rec.get("title") or ""
    year = _year(rec)
    ver = rec.get("version_latest_seen") or ""
    wid = f"{rec.get('id_base')}{ver}"
    wd = " [WITHDRAWN]" if rec.get("withdrawn") else ""
    if rec.get("journal_ref"):
        return (f"{au}. {title}[J]. {rec['journal_ref']}."
                f" Preprint: arXiv:{wid}, https://arxiv.org/abs/{rec.get('id_base')}.{wd}")
    return (f"{au}. {title}[EB/OL]. ({year}). https://arxiv.org/abs/{rec.get('id_base')}"
            f" (arXiv:{wid}).{wd}")


def to_apa(rec):
    """APA 7th：预印本含 arXiv URL；已发表优先期刊信息。"""
    authors = rec.get("authors") or []
    def fmt(name):
        parts = name.split()
        if len(parts) == 1:
            return parts[0]
        return f"{parts[-1]}, " + " ".join(f"{p[0]}." for p in parts[:-1] if p)
    if len(authors) > 20:
        au = ", ".join(fmt(a) for a in authors[:19]) + ", ... " + fmt(authors[-1])
    else:
        au = ", ".join(fmt(a) for a in authors[:-1]) + (", & " + fmt(authors[-1]) if len(authors) > 1 else (fmt(authors[0]) if authors else ""))
    year = _year(rec)
    title = rec.get("title") or ""
    ver = rec.get("version_latest_seen") or ""
    wd = " [WITHDRAWN]" if rec.get("withdrawn") else ""
    if rec.get("journal_ref"):
        doi = f" https://doi.org/{rec['doi']}" if rec.get("doi") else ""
        return f"{au} ({year}). {title}. {rec['journal_ref']}.{doi}{wd}"
    return (f"{au} ({year}). {title} [Preprint]{wd}. arXiv. "
            f"https://arxiv.org/abs/{rec.get('id_base')}"
            + (f" (version {ver})" if ver else ""))


FMT = {"bibtex": to_bibtex, "gbt7714": to_gbt7714, "apa": to_apa}


def smoke():
    base = {
        "id_base": "1706.03762", "version_latest_seen": "v7",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "published": "2017-06-12T17:57:34Z", "updated": "2023-08-02T00:41:18Z",
        "primary_category": "cs.CL", "journal_ref": None, "doi": None, "withdrawn": False,
    }
    b = to_bibtex(base)
    assert "@misc{" in b and "eprint = {1706.03762}" in b and "archivePrefix = {arXiv}" in b
    assert "Version v7" in b
    g = to_gbt7714(base)
    assert "[EB/OL]" in g and "arXiv:1706.03762v7" in g and "et al" in g
    a = to_apa(base)
    assert "[Preprint]" in a and "https://arxiv.org/abs/1706.03762" in a and "Vaswani, A." in a
    pub = dict(base, journal_ref="Nature 590 (2021) 1-10", doi="10.0000/x")
    assert "@article{" in to_bibtex(pub) and "[J]. Nature 590" in to_gbt7714(pub)
    wd = dict(base, withdrawn=True)
    assert "WITHDRAWN" in to_bibtex(wd) and "[WITHDRAWN]" in to_apa(wd) and "[WITHDRAWN]" in to_gbt7714(wd)
    nover = dict(base, version_latest_seen=None)
    assert "arXiv:1706.03762" in to_gbt7714(nover)
    print("SMOKE OK: arxiv_cite 全部断言通过")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="由核验元数据 JSONL 生成标准引文（bibtex/gbt7714/apa）")
    ap.add_argument("files", nargs="*", help="JSONL 文件（缺省读 stdin）")
    ap.add_argument("--format", choices=sorted(FMT))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()
    if not args.format:
        ap.error("非 --smoke 模式必须给 --format")

    texts = []
    if args.files:
        for fp in args.files:
            with open(fp, encoding="utf-8") as f:
                texts.append(f.read())
    else:
        texts.append(sys.stdin.read())

    fn = FMT[args.format]
    for t in texts:
        for line in t.splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("withdrawn"):
                print(f"WARN: {rec.get('id_base')} 已撤稿（WITHDRAWN），原则上不引；确需引用须显式声明撤稿状态",
                      file=sys.stderr)
            if not rec.get("version_latest_seen"):
                print(f"WARN: {rec.get('id_base')} 未锁版本号，引文存在版本漂移风险", file=sys.stderr)
            print(fn(rec))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
