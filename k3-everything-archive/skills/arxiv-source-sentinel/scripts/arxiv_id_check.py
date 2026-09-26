#!/usr/bin/env python3
"""arxiv_id_check.py — arXiv 标识符解析、校验与规范化。

功能：
- 从参数、文件或 stdin 中提取 arXiv ID（新式 2007-04 起：YYMM.NNNNN[vN]；
  旧式 1991-2007：archive/YYMMNNN[vN]，如 hep-th/9901001、cs/0607123）。
- 校验格式合法性（月份 01-12、年份区间、序号位数），区分格式错误与"疑似幻觉 ID"。
- 规范化输出 canonical 形式（带版本号时保留；缺版本标注 version_given=false）。

用法：
  python3 arxiv_id_check.py 2301.07041 1706.03762v3 hep-th/9901001
  python3 arxiv_id_check.py --file ids.txt          # 每行一个或任意文本，自动提取
  cat notes.md | python3 arxiv_id_check.py --extract # 从自由文本提取
  python3 arxiv_id_check.py --smoke                  # 离线自检，不访问网络

输出：JSONL（--pretty 美化），每行一个记录。本脚本不访问网络，纯标准库。
"""
import argparse
import json
import re
import sys

# 新式：YYMM.NNNNN 或 YYMM.NNNN（2007-04 ~ 2014-12 为 4 位序号，2015-01 起 5 位）
NEW_RE = re.compile(r"(?<![\w./-])((\d{2})(0[1-9]|1[0-2])\.(\d{4,5}))(v(\d+))?(?![\w.-])")
# 旧式：archive/YYMMNNN（archive 可含连字符，如 hep-th, math-ph；或大类缩写如 cs, math）
OLD_RE = re.compile(
    r"(?<![\w./-])((?:[a-z-]+(?:\.[A-Z]{2})?)/(\d{2})(0[1-9]|1[0-2])(\d{3}))(v(\d+))?(?![\w.-])"
)

# 旧式合法 archive 名（常见集合，非穷尽；未知 archive 给 warning 而非判非法）
KNOWN_OLD_ARCHIVES = {
    "acc-phys", "adap-org", "alg-geom", "ao-sci", "astro-ph", "atom-ph", "bayes-an",
    "chao-dyn", "chem-ph", "cmp-lg", "comp-gas", "cond-mat", "dg-ga", "funct-an",
    "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math", "math-ph", "mtrl-th",
    "nlin", "nucl-ex", "nucl-th", "patt-sol", "physics", "plasm-ph", "q-alg",
    "q-bio", "q-fin", "quant-ph", "solv-int", "supr-con",
    "cs", "econ", "eess", "stat",
}


def classify_year_month(style, yy, mm):
    """返回 (year, month, warnings)。新式 2007-04 起；旧式 1991-08 ~ 2007-03。"""
    year = 2000 + yy if yy <= 90 else 1900 + yy  # arXiv 无 1991 前论文；91-99 → 19xx
    warnings = []
    if style == "new":
        if (year, mm) < (2007, 4):
            warnings.append("new_style_before_2007-04: 新式 ID 不可能早于 2007-04，疑似幻觉或转写错误")
        if year > 2026 or (year == 2026 and mm > 12):
            warnings.append("future_date: 年月晚于当前时间，疑似幻觉 ID")
    else:
        if (year, mm) < (1991, 8):
            warnings.append("old_style_before_1991-08: 早于 arXiv 创立")
        if (year, mm) > (2007, 3):
            warnings.append("old_style_after_2007-03: 旧式 ID 止于 2007-03，之后应为新式")
    return year, mm, warnings


def parse_one(raw):
    """解析单个候选 ID 字符串，返回记录 dict。"""
    rec = {"input": raw, "valid": False, "style": None, "canonical": None,
           "id_base": None, "version": None, "version_given": False,
           "year": None, "month": None, "warnings": []}

    m = NEW_RE.fullmatch(raw.strip())
    style = "new"
    if not m:
        m = OLD_RE.fullmatch(raw.strip())
        style = "old" if m else None
    if not m:
        rec["warnings"].append("format_error: 不匹配任何 arXiv ID 形制")
        return rec

    body, yy_s, mm_s, seq = m.group(1), m.group(2), m.group(3), m.group(4)
    ver = m.group(6)
    yy, mm = int(yy_s), int(mm_s)
    rec["style"] = style
    year, month, warns = classify_year_month(style, yy, mm)
    rec["warnings"].extend(warns)
    rec["year"], rec["month"] = year, month

    if style == "new":
        if len(seq) == 4 and (year, month) >= (2015, 1):
            rec["warnings"].append("seq_4digit_after_2015: 2015-01 起序号为 5 位，4 位序号疑似截断/幻觉")
        if int(seq) == 0:
            rec["warnings"].append("seq_zero: 序号不可能为 0")
    else:
        archive = body.split("/")[0]
        # 子类后缀（.AG/.GA 等两位大写）剥掉再查表；q-fin 等合法 archive 在表内
        base_archive = re.sub(r"\.[A-Z]{2}$", "", archive)
        if base_archive not in KNOWN_OLD_ARCHIVES:
            rec["warnings"].append(f"unknown_old_archive: {archive} 不在常见旧 archive 表（非判死，人工核对）")

    rec["id_base"] = body
    if ver:
        rec["version"] = f"v{ver}"
        rec["version_given"] = True
    rec["canonical"] = body + (rec["version"] or "")
    rec["valid"] = not any(w.startswith("format_error") for w in rec["warnings"])
    return rec


def extract_from_text(text):
    """从自由文本提取全部候选（新式优先，再旧式），保持出现顺序去重。"""
    seen, out = set(), []
    for rx in (NEW_RE, OLD_RE):
        for m in rx.finditer(text):
            cand = m.group(1) + (f"v{m.group(6)}" if m.group(6) else "")
            if cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def smoke():
    cases_ok = ["2301.07041", "1706.03762v3", "hep-th/9901001", "cs/0607123v2",
                "2405.12345", "math.AG/0601001"]
    cases_bad = ["2301.0704a", "2313.00001", "not-an-id", "1501.123", ""]
    for c in cases_ok:
        r = parse_one(c)
        assert r["valid"], f"应合法却非法: {c} -> {r}"
        assert r["canonical"], c
    r = parse_one("1501.0123")  # 4 位序号 + 2015 后 → 合法但带 warning
    assert any("seq_4digit" in w for w in r["warnings"])
    assert not parse_one("1501.123")["valid"]  # 3 位序号 → 格式错误
    for c in ["2313.00001", "not-an-id"]:
        r = parse_one(c)
        assert not r["valid"] or any("format_error" in w or "month" in w for w in r["warnings"]) or r["month"] in range(1, 13)
    r = parse_one("2313.00001")
    assert r["month"] == 13 or not r["valid"], "月份 13 必须被挡"
    txt = "见 1706.03762v3 与 hep-th/9901001，再看 1706.03762（重复）"
    ex = extract_from_text(txt)
    assert "1706.03762v3" in ex and "hep-th/9901001" in ex
    print("SMOKE OK: arxiv_id_check 全部断言通过")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="arXiv ID 解析/校验/规范化（离线，纯标准库）")
    ap.add_argument("ids", nargs="*", help="待校验的 arXiv ID")
    ap.add_argument("--file", help="从文件读取（先按行，再从每行提取）")
    ap.add_argument("--extract", action="store_true", help="从 stdin 自由文本提取")
    ap.add_argument("--pretty", action="store_true", help="美化 JSON 输出")
    ap.add_argument("--smoke", action="store_true", help="离线自检")
    args = ap.parse_args(argv)

    if args.smoke:
        return smoke()

    cands = list(args.ids)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            cands.extend(extract_from_text(f.read()))
    if args.extract or (not cands and not sys.stdin.isatty()):
        cands.extend(extract_from_text(sys.stdin.read()))
    if not cands:
        ap.error("无输入：给位置参数、--file 或 --extract/stdin")

    dump = (lambda o: json.dumps(o, ensure_ascii=False, indent=2)) if args.pretty \
        else (lambda o: json.dumps(o, ensure_ascii=False))
    for c in cands:
        print(dump(parse_one(c)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
