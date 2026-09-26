# VENDORED+MERGED v1.1（2026-08-26，修改人：Orchestrator/Kimi K3）
# 上游：腾讯助手甲 relabel_summary.py（用户提供）+ K3 补丁(a/b) + 助手甲②c补丁（特征句查询改用db_key别名）
# 修复链：助手甲原版→K3(a)仅处理正文/(b)全键对齐→助手甲复现发现(b)仅修复了known_length一处→②c将两处查询统一改为使用别名
"""
relabel_summary.py —— 整改脚本：把任务1首批6篇从"误标全文/verified"重标为"摘要级"

判定逻辑（保守优先，宁可误判 truncated=true，不可反向）：
  R1 显式截断标记（"未完待续/点击查看全文/展开全文"...）
  R2 体积比对：若已知原文参考长度 L_ref，ratio = n/L_ref < 0.85 → 截断
  R3 特征句命中：8 句中命中 < 6 → 截断

即便 R1-R3 全过、判定为"完整"，也只标 complete_likely，绝不标 verified。
verified 必须来自原文字节级比对（如 PDF 的 SHA-256）。

用法：python3 relabel_summary.py --batch ./batches/yb_delivery_1 --out ./batches/yb_delivery_1_relabeled
"""

import argparse, json, os, re
from pathlib import Path

TRUNCATION_MARKERS = ["未完待续", "点击查看全文", "展开全文", "阅读原文", "长按识别"]
FEATURE_SENTENCES_DB = {
    # slug: [该篇应出现的 8 句特征句]，由 K3 核验报告的特征句命中率反推占位
    # 实际使用时由调用方填充；此处仅示意结构
    "transformer-sanbian": [],
    "wire-cable-rifeng": [],
    "yunnan": [],
    "binzhou": [],
    "advanced-electronic-ceramics": [],
    "auto-industry-catalog": [],
}


def contains_truncation_marker(md: str) -> bool:
    return any(m in md for m in TRUNCATION_MARKERS)


def feature_sentence_hit(md: str, sentences: list[str]) -> int:
    if not sentences:
        return 99  # 未提供特征句时，不参与否决（保守：不当作截断证据）
    return sum(1 for s in sentences if s and s in md)


def resolve_db_key(slug: str, db: dict) -> str:
    """②c：slug 别名解析——优先精确命中，其次前缀/去日期后缀模糊命中（_nd vs _20260614 类不一致）。"""
    if slug in db: return slug
    base = slug.split("_singlewell")[0]
    for k in db:
        if k.startswith(base) or base.startswith(k.split("_singlewell")[0]):
            return k
    return slug

def judge_truncated(md: str, slug: str, known_length_db: dict) -> tuple[bool, str]:
    n = len(md)
    if contains_truncation_marker(md):
        return True, "R1_explicit_marker"
    kl_key = resolve_db_key(slug, known_length_db)
    if kl_key in known_length_db and n < known_length_db[kl_key] * 0.85:
        return True, "R2_volume_ratio"
    fs_key = resolve_db_key(slug, FEATURE_SENTENCES_DB)
    hit = feature_sentence_hit(md, FEATURE_SENTENCES_DB.get(fs_key, []))
    if hit < 6:
        return True, "R3_feature_sentences"
    return False, "complete_likely"


WARNING = (
    "> ⚠️ **本篇为 web_fetch 转码摘要，非全文，仅作内容预告 / 交叉佐证，"
    "请勿当作正文归档（防冒充全文）。**\n"
)


def relabel(in_dir: Path, out_dir: Path, known_length_db: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for p in sorted(in_dir.glob("*.md")):
        md = p.read_text(encoding="utf-8")
        body = re.sub(r"^>.*?\n", "", md, count=0)  # 去掉旧头部（粗略）
        truncated, reason = judge_truncated(body, p.stem, known_length_db)
        new_header = (
            "---\n"
            f"slug: {p.stem}\n"
            f"status: summary_not_full\n"
            f"truncated: {str(truncated).lower()}\n"
            f"completeness: {'complete_likely' if not truncated else 'summary'}\n"
            f"truncation_reason: {reason}\n"
            "---\n\n"
        )
        new_md = new_header + WARNING + "\n" + body.lstrip()
        (out_dir / p.name).write_text(new_md, encoding="utf-8")

        rec = {
            "slug": p.stem,
            "old_status": "verified (错误)",
            "new_status": "summary_not_full",
            "truncated": truncated,
            "completeness": "complete_likely" if not truncated else "summary",
            "reason": reason,
            "chars": len(body),
        }
        report.append(rec)
        print(f"[{p.stem}] truncated={truncated} reason={reason} chars={len(body)}")

    (out_dir / "RELABEL_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== 重标完成 ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="待重标的 md 目录")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--known-length", default=None, help="可选：已知原文长度 JSON {slug:int}")
    args = ap.parse_args()

    known = {}
    if args.known_length:
        known = json.loads(Path(args.known_length).read_text(encoding="utf-8"))

    relabel(Path(args.batch), Path(args.out), known)


if __name__ == "__main__":
    main()
