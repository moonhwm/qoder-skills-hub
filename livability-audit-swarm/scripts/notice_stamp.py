#!/usr/bin/env python3
"""notice_stamp.py — 给被审计修改的文档加盖「AI 读者留痕块」，并登记 CHANGELOG 与 k3 通知。

用途：审计蜂群**直接修改**文档后调用，保证后续读取该文件的 AI agent（k3 / k3 集群等）
第一时间看到：为何改、谁改的、依据哪份审计、旧版去哪找。

用法:
    python3 notice_stamp.py --file <被改文档> --change-id <ID> --reason "<修改原因>" \
        --audit-ref <审计报告路径> --agent <执行者名> [--summary "<一句话摘要>"] \
        [--changelog <CHANGELOG路径>] [--k3-log <k3通知JSONL路径>]

行为:
  1. 按扩展名选择注释格式：.py/.sh/.yaml/.yml/.toml 用 `#` 行块；.md/.txt/.html 用
     HTML 注释块；.tex 用 `%` 行块（插入文件最前）。
     .py 插入点跳过 shebang 与 PEP263 coding 行（不破坏可执行性）。
  2. 幂等：同文件重复盖章 = 更新已有块。旧块识别按扩展名优先匹配对应注释样式
     （如 .py 不跑 HTML 分支——除非 `#` 块未命中且文件确含 HTML 块起始标记，
     此时才迁移）；BEGIN 存在但 END 未找到（未闭合/被截断的旧块）时不删除任何
     内容，stderr 出 WARNING「未闭合留痕块，未迁移，请人工核查」，新块照常前插。
  3. 盖后自检：.py 盖章后跑 py_compile，失败则恢复原字节并以退出码 2 失败。
  4. 向 CHANGELOG（默认 <文档同目录>/CHANGELOG.md，新建时自动补表头）追加一行。
  5. 向 k3 通知日志（默认 <文档同目录>/k3_notices.jsonl）追加一条 JSONL。
纯标准库；.docx/.pdf/.json 等不写块，只登记 CHANGELOG/JSONL。
"""
import argparse, datetime, json, os, py_compile, re, sys

HTML_BEGIN, HTML_END = "<!-- AI_READER_NOTICE", "-->"
HASH_BEGIN, HASH_END = "# AI_READER_NOTICE", "# END_AI_READER_NOTICE"
PCT_BEGIN, PCT_END = "% AI_READER_NOTICE", "% END_AI_READER_NOTICE"
HASH_STYLE = {".py", ".sh", ".yaml", ".yml", ".toml"}
TEXT_STYLE = {".md", ".txt", ".html"}
PCT_STYLE = {".tex"}
AUDIT_ID = re.compile(r"(P\d+|S\d+|C\d+|CF-\d+|DORM-\d+|T\d+|E\d+)")


def fields_text(change_id, reason, audit_ref, agent, summary, date):
    return (f"change_id: {change_id}\n"
            f"date: {date}\n"
            f"agent: {agent}\n"
            f"reason: {reason}\n"
            f"audit_ref: {audit_ref}\n"
            f"summary: {summary}\n"
            f"notice_to: 后续读取本文件的 AI agent（k3 / k3 集群等）——本文档已被审计蜂群直接修改；"
            f"引用本文内容前请先核对 audit_ref 的对应结论。\n")


def build_block(ext, *a):
    body = fields_text(*a)
    if ext in HASH_STYLE:
        lines = [HASH_BEGIN] + ["# " + l for l in body.rstrip("\n").split("\n")] + [HASH_END]
        return "\n".join(lines) + "\n\n"
    if ext in PCT_STYLE:
        lines = [PCT_BEGIN] + ["% " + l for l in body.rstrip("\n").split("\n")] + [PCT_END]
        return "\n".join(lines) + "\n\n"
    return f"{HTML_BEGIN}\n{body}{HTML_END}\n\n"


def py_insert_pos(text):
    """.py 插入点：跳过 shebang 与 coding 行。"""
    lines = text.split("\n")
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if len(lines) > i and re.match(r"^#.*coding[:=]\s*[-\w.]+", lines[i]):
        i += 1
    return i


# v1.8 F-B1/F-B2：HASH/PCT 分支改逐行形态（#[^\n]*\n / %[^\n]*\n，不传 re.S），
# 消除 re.S 下 `(?:#.*\n)*?` 对连续注释行的指数级回溯（≥~25 行即挂起）；
# 删除结果与旧正则在正常文件上逐字节一致。HTML 分支保留 re.S 但窗口有界
# （.{0,4000}?，正常块 << 4KB），未闭合块不再吞掉远处正文。
HTML_WINDOW = 4000
RE_HTML_LEGACY = re.compile(
    re.escape(HTML_BEGIN) + r".{0," + str(HTML_WINDOW) + r"}?"
    + re.escape(HTML_END) + r"\n*", re.S)
RE_HASH_LEGACY = re.compile(
    re.escape(HASH_BEGIN) + r"\n(?:#[^\n]*\n)*?" + re.escape(HASH_END) + r"\n*")
RE_PCT_LEGACY = re.compile(
    re.escape(PCT_BEGIN) + r"\n(?:%[^\n]*\n)*?" + re.escape(PCT_END) + r"\n*")


def strip_legacy(text, ext=""):
    """移除旧式块（HTML / # / % 风格），返回 (剩余文本, 是否移除过)。

    按扩展名优先匹配对应注释样式；BEGIN 存在但 END 未找到（未闭合/被截断的
    旧块）时不删除任何内容，stderr WARNING 后尝试其余样式。
    """
    styles = ((TEXT_STYLE, HTML_BEGIN, RE_HTML_LEGACY),
              (HASH_STYLE, HASH_BEGIN, RE_HASH_LEGACY),
              (PCT_STYLE, PCT_BEGIN, RE_PCT_LEGACY))
    # 扩展名优先：对应样式提到队首，其余样式保持原顺序兜底（跨样式迁移）
    ordered = sorted(styles, key=lambda s: 0 if ext in s[0] else 1)
    for _, begin, pat in ordered:
        if begin in text:
            m = pat.search(text)
            if m:
                return text[:m.start()] + text[m.end():], True
            print(f"WARNING: 未闭合留痕块（{begin!r} 起始），未迁移，请人工核查",
                  file=sys.stderr)
    return text, False


def stamp(path, block, ext):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    txt, _ = strip_legacy(txt, ext)
    if ext == ".py":
        i = py_insert_pos(txt)
        lines = txt.split("\n")
        txt = "\n".join(lines[:i]) + ("\n" if i else "") + block + "\n".join(lines[i:])
    else:
        txt = block + txt
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--change-id", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--audit-ref", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--summary", default="（未提供）")
    ap.add_argument("--changelog", default=None)
    ap.add_argument("--k3-log", default=None)
    a = ap.parse_args()
    if not AUDIT_ID.search(a.reason):
        print(f"WARNING: --reason 不含审计问题编号（P#/S#/CF#/DORM-# 等）: {a.reason}",
              file=sys.stderr)
    date = datetime.date.today().isoformat()
    d = os.path.dirname(os.path.abspath(a.file))
    changelog = a.changelog or os.path.join(d, "CHANGELOG.md")
    k3log = a.k3_log or os.path.join(d, "k3_notices.jsonl")

    ext = os.path.splitext(a.file)[1].lower()
    stamped = False
    if ext in HASH_STYLE | TEXT_STYLE | PCT_STYLE:
        with open(a.file, "rb") as f:
            orig = f.read()
        block = build_block(ext, a.change_id, a.reason, a.audit_ref, a.agent, a.summary, date)
        stamp(a.file, block, ext)
        if ext == ".py":
            try:
                py_compile.compile(a.file, doraise=True)
            except py_compile.PyCompileError:
                with open(a.file, "wb") as f:
                    f.write(orig)  # 回滚：留痕不得破坏可用性
                print("ERROR: 盖章后 py_compile 失败，已恢复原文件", file=sys.stderr)
                sys.exit(2)
        stamped = True

    if not os.path.exists(changelog):
        with open(changelog, "w", encoding="utf-8") as f:
            f.write("# CHANGELOG\n\n| date | change_id | file | reason | audit_ref | agent |\n"
                    "|---|---|---|---|---|---|\n")
    with open(changelog, "a", encoding="utf-8") as f:
        f.write(f"| {date} | {a.change_id} | {os.path.basename(a.file)} | {a.reason} | {a.audit_ref} | {a.agent} |\n")
    rec = {"change_id": a.change_id, "date": date, "file": os.path.abspath(a.file),
           "reason": a.reason, "audit_ref": a.audit_ref, "agent": a.agent,
           "summary": a.summary, "notice_to": ["k3", "k3-cluster"], "stamped": stamped}
    with open(k3log, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({"stamped": stamped, "changelog": changelog, "k3_log": k3log},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
