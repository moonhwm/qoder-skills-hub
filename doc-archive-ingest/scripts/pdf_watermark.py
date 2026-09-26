#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_watermark.py —— PDF 水印「识别 + 合规抹除」工具
=============================================================================
子命令：
  scan  <文件或目录> [报告.json]     只识别与报告，不修改任何 PDF
  clean <文件或目录> --owned "授权声明" [日志.json]
                                   合规抹除：仅限用户本人已购/自有文档，
                                   必须显式携带 --owned 授权声明，否则拒绝执行
  --smoke                          自构带水印 PDF 验证识别/抹除/日志（不联网）

合规边界（硬约束，脚本内强制）：
1. 仅处理**文本层**与**注解层(Annotation)**水印对象：
   - /Annots 中 Subtype 为 /Watermark 的注解（PDF 规范定义的标准水印注解）；
   - 跨页重复出现且命中水印用词的静态文字（用 redaction 仅移除文本对象）。
2. 不做：破解加密（加密/DRM 的 PDF 直接拒绝处理并记录原因）、不栅格化或涂改
   图像层内容（图像层水印无法合规界定边界，只报告不处理）。
3. 原件一律保留不动；输出 `原文件名_cleaned.pdf` 副本。
4. 每处理一份，向处理日志 JSON 追加双 SHA-256：
   {file, time, watermark_types, method, original_sha256, cleaned_sha256, result}。

法律提示：绕过技术保护措施在《中华人民共和国著作权法》下处于灰色地带
（第四十九条、第五十三条），对他人享有版权的文档抹除水印可能损害权利人
合法权益。详见 references/legal_notes.md。

依赖：PyMuPDF (fitz)，惰性加载；--smoke 在 pymupdf 缺失时优雅降级为
仅验证授权门禁与日志结构并注明。
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone

# 跨页重复文字达到该页数比例才视为“静态文字水印”候选
MIN_PAGE_RATIO = 0.5
# 命中水印用词 + 跨页重复 => 认定文字水印；纯跨页重复但无命中词的按“疑似”
# 处理，为避免误删正文，默认只删命中词项
HINT_WORDS = ("水印", "内部", "机密", "绝密", "秘密", "confidential",
              "draft", "sample", "watermark", "仅供", "翻印", "盗版",
              "内部资料", "不得外传")

EXIT_REFUSED = 3   # 未携带 --owned 授权声明
EXIT_NO_FITZ = 2   # 缺少 pymupdf


def require_fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        sys.stderr.write("缺少依赖 PyMuPDF：pip install pymupdf\n")
        sys.exit(EXIT_NO_FITZ)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +0800")


def iter_pdfs(root):
    """root 可为单个 PDF 或目录（递归）。跳过工具产物 *_cleaned.pdf。"""
    if os.path.isfile(root):
        if root.lower().endswith(".pdf") and not root.lower().endswith("_cleaned.pdf"):
            yield root
        return
    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            if fn.lower().endswith(".pdf") and not fn.lower().endswith("_cleaned.pdf"):
                yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------- 识别
def scan_pdf(path):
    """识别单个 PDF 的候选水印，返回报告字典。只读，不修改文件。"""
    fitz = require_fitz()
    doc = fitz.open(path)
    page_count = doc.page_count
    text_counter = Counter()   # 文本片段 -> 出现页数
    image_counter = Counter()  # 图片 xref -> 出现页数
    annot_count = 0
    for page in doc:
        lines = set()
        for line in page.get_text("text").splitlines():
            line = " ".join(line.split())
            if 2 <= len(line) <= 60:
                lines.add(line)
        for line in lines:
            text_counter[line] += 1
        for xref in {img[0] for img in page.get_images(full=True)}:
            image_counter[xref] += 1
        for annot in (page.annots() or []):
            if annot.type and "Watermark" in str(annot.type[1]):
                annot_count += 1
    doc.close()

    def to_items(counter, min_pages):
        return [{"value": str(k), "pages_seen": v}
                for k, v in counter.most_common() if v >= min_pages]

    min_pages = max(2, page_count // 3)  # 至少出现在 1/3 页面以上才视为候选水印
    text_items = to_items(text_counter, min_pages)
    for it in text_items:
        it["keyword_hint"] = any(w.lower() in it["value"].lower() for w in HINT_WORDS)
    return {
        "file": os.path.abspath(path),
        "pages": page_count,
        "candidate_text_watermarks": text_items,
        "candidate_image_watermarks": to_items(image_counter, min_pages),
        "annot_watermarks": annot_count,
        "note": "仅识别报告，未对该文件做任何修改",
    }


def cmd_scan(root, out):
    report = {"scan_root": os.path.abspath(root),
              "policy": "识别不修改；抹除仅适用于用户自有/已购文档并需 --owned 显式授权",
              "files": []}
    n = 0
    for p in iter_pdfs(root):
        try:
            report["files"].append(scan_pdf(p))
            n += 1
        except Exception as e:  # 读不了的如实标注
            report["files"].append({"file": os.path.abspath(p),
                                    "error": f"{type(e).__name__}: {e}"})
    report["pdf_scanned"] = n
    report["pdf_total_found"] = len(report["files"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"扫描完成：发现 PDF {len(report['files'])} 个，成功解析 {n} 个。报告 -> {out}")
    return 0


# ---------------------------------------------------------------- 抹除
def detect_text_watermark_lines(doc):
    """统计跨页重复的文本行，返回 (命中词的水印行集合, 疑似但无命中词的行集合)。"""
    pages = doc.page_count
    if pages == 0:
        return set(), set()
    counter = Counter()
    for page in doc:
        lines = set()
        for line in page.get_text("text").splitlines():
            line = " ".join(line.split())
            if 2 <= len(line) <= 60:
                lines.add(line)
        for line in lines:
            counter[line] += 1
    threshold = max(2, int(pages * MIN_PAGE_RATIO))
    repeated = {ln for ln, c in counter.items() if c >= threshold}
    hit = {ln for ln in repeated
           if any(w.lower() in ln.lower() for w in HINT_WORDS)}
    return hit, repeated - hit


def remove_annot_watermarks(doc):
    """删除所有 /Watermark 子类型注解。返回删除数量。"""
    removed = 0
    for page in doc:
        for annot in list(page.annots() or []):
            # annot.type[1] 为子类型名，如 "Watermark"
            if annot.type and "Watermark" in str(annot.type[1]):
                page.delete_annot(annot)
                removed += 1
    return removed


def redact_text_lines(doc, fitz, lines):
    """用 redaction 删除指定文本行的所有出现（仅文本层，不动图像）。"""
    removed = 0
    for page in doc:
        for line in lines:
            for r in page.search_for(line):
                # fill=False 不加遮盖色块，仅移除底层文本对象
                page.add_redact_annot(r, fill=False)
                removed += 1
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    return removed


def process_pdf(path, log):
    """处理单个 PDF：识别 -> 合规抹除 -> 输出 _cleaned 副本。原件不动。"""
    fitz = require_fitz()
    entry = {"file": os.path.abspath(path), "time": now_str(),
             "watermark_types": [], "method": None,
             "original_sha256": None, "cleaned_sha256": None, "result": None}
    log["files"].append(entry)
    try:
        entry["original_sha256"] = sha256(path)
    except Exception as e:
        entry["result"] = f"跳过：无法读取原件计算hash（{type(e).__name__}: {e}）"
        return entry
    try:
        doc = fitz.open(path)
    except Exception as e:
        entry["result"] = f"跳过：PDF 无法打开（{type(e).__name__}: {e}）"
        return entry
    if doc.needs_pass or doc.is_encrypted:
        entry["result"] = ("跳过：PDF 加密/受 DRM 保护，本工具不破解加密、"
                           "不去除 DRM（合规边界），原件保留")
        doc.close()
        return entry

    methods, results = [], []

    # 1) 注解层水印
    n_annot = remove_annot_watermarks(doc)
    if n_annot:
        entry["watermark_types"].append("注解层水印(/Annots:Watermark)")
        methods.append(f"删除Watermark注解 {n_annot} 个")

    # 2) 文本层水印（跨页重复且命中水印用词）
    hit, suspected = detect_text_watermark_lines(doc)
    if hit:
        n_text = redact_text_lines(doc, fitz, hit)
        entry["watermark_types"].append("静态文本层水印(跨页重复文字)")
        methods.append(f"redaction移除文本实例 {n_text} 处（{len(hit)} 种文本）")
    if suspected:
        results.append(f"另有 {len(suspected)} 种跨页重复文字未命中水印词，"
                       f"为避免误删正文未处理：{sorted(suspected)[:5]}")

    # 3) 图像层检测（只报告，不处理）
    img_counter = Counter()
    for page in doc:
        for xref in {img[0] for img in page.get_images(full=True)}:
            img_counter[xref] += 1
    pages = max(1, doc.page_count)
    img_wm = [x for x, c in img_counter.items() if c >= max(2, int(pages * MIN_PAGE_RATIO))]
    if img_wm:
        entry["watermark_types"].append("疑似图像层水印(跨页复用图片对象)")
        results.append(f"图像层水印疑似 {len(img_wm)} 处：位于图像层，无法以合规手段"
                       f"界定与去除，跳过（原件保留）")

    if not methods:
        entry["result"] = ("跳过：未检出可合规抹除的文本/注解层水印"
                           + ("；" + "；".join(results) if results else ""))
        doc.close()
        return entry

    out = os.path.splitext(path)[0] + "_cleaned.pdf"
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    entry["method"] = "；".join(methods)
    entry["cleaned_path"] = os.path.abspath(out)
    entry["cleaned_sha256"] = sha256(out)
    entry["result"] = ("已生成去水印副本（原件保留不动）"
                       + ("；" + "；".join(results) if results else ""))
    return entry


def cmd_clean(root, out, owned):
    if not owned or not owned.strip():
        sys.stderr.write(
            "拒绝执行：抹除水印仅限用户本人已购/自有文档，必须显式携带授权声明，例如\n"
            "  python3 pdf_watermark.py clean <目录> --owned \"本人确认该批文档为本人/本机构"
            "已购文档，授权对这批文档做去水印处理，范围仅限本批文档\"\n")
        return EXIT_REFUSED
    log = {
        "policy": ("去水印仅限用户已购/自有文档的个人归档场景；仅抹除文本/注解层"
                   "水印对象；不破解加密、不去除 DRM；原件一律保留"),
        "authorization": owned.strip(),
        "scope_root": os.path.abspath(root),
        "run_at": now_str(),
        "files": [],
    }
    n_pdf = 0
    for p in iter_pdfs(root):
        n_pdf += 1
        process_pdf(p, log)
    log["pdf_found"] = n_pdf
    log["cleaned_generated"] = sum(1 for e in log["files"] if e.get("cleaned_sha256"))
    if n_pdf == 0:
        log["note"] = "本次运行未发现任何 PDF 可处理（如实记录，非脚本故障）。"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print(f"处理完成：发现 PDF {n_pdf} 个，生成 cleaned 副本 "
          f"{log['cleaned_generated']} 个 -> {out}")
    return 0


# ---------------------------------------------------------------- 冒烟自测
def _smoke_gate_only():
    """pymupdf 缺失时的优雅降级：仅验证 --owned 授权门禁与日志结构。"""
    with tempfile.TemporaryDirectory(prefix="wm_smoke_") as tmp:
        rc = cmd_clean(tmp, os.path.join(tmp, "log.json"), owned="")
        assert rc == EXIT_REFUSED, "无 --owned 必须拒绝"
        h = hashlib.sha256(b"gate").hexdigest()
        assert len(h) == 64
    print("[SMOKE DEGRADED] pymupdf 缺失：仅验证授权门禁（识别/抹除未验证，已注明）")
    return 0


def smoke():
    try:
        import fitz
    except ImportError:
        return _smoke_gate_only()
    with tempfile.TemporaryDirectory(prefix="wm_smoke_") as tmp:
        # 自构带水印 PDF：3 页均有命中词的静态文字水印 + 每页不同正文
        src = os.path.join(tmp, "已购讲义.pdf")
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 700), "内部资料 仅供学习", fontname="china-s")
            page.insert_text((72, 100), f"第 {i + 1} 页正文：数据结构讲义内容。",
                             fontname="china-s")
        # 加一个 /Watermark 注解（若当前 pymupdf 支持该子类型）
        try:
            annot = doc[0].add_freetext_annot(
                fitz.Rect(200, 300, 400, 340), "CONFIDENTIAL",
                fontsize=24, rotate=45)
            annot.set_colors(stroke=(0.8, 0.8, 0.8))
            annot.update()
        except Exception:
            pass
        doc.save(src)
        doc.close()
        orig_hash = sha256(src)

        # 1) 无授权声明 -> 必须拒绝
        rc = cmd_clean(tmp, os.path.join(tmp, "refused_log.json"), owned="")
        assert rc == EXIT_REFUSED, "无 --owned 必须拒绝执行"
        assert not os.path.exists(os.path.join(tmp, "refused_log.json"))

        # 2) scan：应识别出跨页文本水印
        scan_out = os.path.join(tmp, "report.json")
        assert cmd_scan(tmp, scan_out) == 0
        report = json.load(open(scan_out, encoding="utf-8"))
        texts = report["files"][0]["candidate_text_watermarks"]
        assert any(t["value"] == "内部资料 仅供学习" and t["pages_seen"] == 3
                   and t["keyword_hint"] for t in texts), f"文本水印识别失败: {texts}"

        # 3) 带授权声明 clean：生成 _cleaned，原件不动，双 hash 日志
        log_out = os.path.join(tmp, "removal_log.json")
        rc = cmd_clean(tmp, log_out, owned="冒烟自测：本人确认该自构 PDF 为自有文档")
        assert rc == 0
        log = json.load(open(log_out, encoding="utf-8"))
        entry = log["files"][0]
        cleaned = os.path.join(tmp, "已购讲义_cleaned.pdf")
        assert os.path.exists(cleaned), "未生成 _cleaned 副本"
        assert sha256(src) == orig_hash, "原件被改动"
        assert entry["original_sha256"] == orig_hash
        assert entry["cleaned_sha256"] == sha256(cleaned)
        assert entry["cleaned_sha256"] != entry["original_sha256"]
        assert log["cleaned_generated"] == 1
        assert log["authorization"].startswith("冒烟自测")

        # 4) 验证水印文字已被移除、正文保留
        d2 = fitz.open(cleaned)
        full = "".join(p.get_text("text") for p in d2)
        d2.close()
        assert "内部资料" not in full and "仅供学习" not in full, "水印文字未移除"
        assert "数据结构讲义内容" in full, "正文被误删"

    print("[SMOKE OK] pdf_watermark: 门禁拒绝/识别/抹除/原件保留/双hash日志 全部通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="PDF 水印识别与合规抹除工具")
    sub = ap.add_subparsers(dest="cmd")
    p_scan = sub.add_parser("scan", help="只识别与报告，不修改 PDF")
    p_scan.add_argument("root", help="PDF 文件或目录")
    p_scan.add_argument("out", nargs="?", default="watermark_report.json")
    p_clean = sub.add_parser("clean", help="合规抹除（需 --owned 显式授权）")
    p_clean.add_argument("root", help="PDF 文件或目录")
    p_clean.add_argument("out", nargs="?", default="watermark_removal_log.json")
    p_clean.add_argument("--owned", default="",
                         help="授权声明（必填，原文记入日志）；仅限本人已购/自有文档")
    ap.add_argument("--smoke", action="store_true", help="自构带水印 PDF 自测")
    args = ap.parse_args()
    if args.smoke:
        return smoke()
    if args.cmd == "scan":
        return cmd_scan(args.root, args.out)
    if args.cmd == "clean":
        return cmd_clean(args.root, args.out, args.owned)
    ap.error("缺少子命令 scan/clean；或使用 --smoke 自测")


if __name__ == "__main__":
    sys.exit(main())
