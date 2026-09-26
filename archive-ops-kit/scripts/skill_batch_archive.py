#!/usr/bin/env python3
"""skill_batch_archive.py — 批量解压 + 简化归档一条龙（纯标准库）

流程：递归解压嵌套 zip（CRC 校验、深度限制防 zip quine）
   → 与指定参照目录逐文件 MD5 比对（判定新旧差异）
   → 生成简化归档登记表（markdown）
   → 把原始子包打成单一带日期封存 zip + README

用法：
  python3 skill_batch_archive.py 源包.zip \
      --reference <技能安装位> \
      --workdir  <输出区>/batch_run \
      --seal     <上传区>/skill-legacy-archive-YYYY-MM-DD.zip
  python3 skill_batch_archive.py --smoke   # 合成样例自检
"""
import argparse, hashlib, json, sys, zipfile
from datetime import date
from pathlib import Path

MAX_DEPTH = 5  # 防 zip quine 死循环


def unpack_recursive(zpath: Path, dest: Path, depth: int = MAX_DEPTH, log=None):
    """递归解压 zip 到 dest，并下钻其中的子 zip。返回 (包名, 状态, 文件数) 列表。"""
    log = log if log is not None else []
    if depth < 0 or not zipfile.is_zipfile(zpath):
        return log
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        bad = z.testzip()
        if bad is not None:
            log.append({"pkg": zpath.name, "status": f"crc_fail:{bad}", "files": 0})
            return log
        z.extractall(dest)
    subs = sorted(dest.glob("*.zip"))
    if subs:
        log.append({"pkg": zpath.name, "status": "ok", "files": -1})  # 外层
        for f in subs:
            unpack_recursive(f, f.with_suffix(""), depth - 1, log)
    else:
        n = sum(1 for p in dest.rglob("*") if p.is_file())
        log.append({"pkg": zpath.name, "status": "ok", "files": n})
    return log


def file_hashes(d: Path):
    return {str(p.relative_to(d)): hashlib.md5(p.read_bytes()).hexdigest()
            for p in d.rglob("*") if p.is_file()} if d.is_dir() else {}


def audit(extract_root: Path, reference_dirs):
    """每个解出的技能目录 vs 参照目录（按优先级取第一个命中）。返回逐技能差异表。"""
    rows = []
    for d in sorted(extract_root.iterdir()):
        if not d.is_dir():
            continue
        ref = next((r / d.name for r in reference_dirs if (r / d.name / "SKILL.md").exists()), None)
        oh = file_hashes(d)
        if ref is None:
            rows.append({"skill": d.name, "files": len(oh), "ref": None,
                         "verdict": "参照库无此技能（孤儿包，人工裁决）"})
            continue
        nh = file_hashes(ref)
        same = set(oh) & set(nh)
        identical = sum(1 for f in same if oh[f] == nh[f])
        changed = [f for f in same if oh[f] != nh[f]]
        only_old, only_new = sorted(set(oh) - set(nh)), sorted(set(nh) - set(oh))
        if not changed and not only_old and not only_new:
            verdict = "与现装版逐字节一致 → 封存"
        elif not only_old and all(f.endswith("SKILL.md") for f in changed):
            verdict = f"仅 SKILL.md 有新版迭代（+{len(only_new)} 新文件）→ 以新版为准，封存旧包"
        else:
            verdict = f"结构差异（改{len(changed)}/仅旧{len(only_old)}/仅新{len(only_new)}）→ 人工复核后封存"
        rows.append({"skill": d.name, "files": len(oh), "ref": str(ref), "verdict": verdict})
    return rows


def seal(source_zips, seal_path: Path, registry_md: str, readme: str):
    """把原始子包 + README + 登记表打成一个封存 zip。"""
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(seal_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in source_zips:
            z.write(p, p.name)
        z.writestr("README.md", readme)
        z.writestr("registry.md", registry_md)
    return seal_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", help="嵌套压缩包路径")
    ap.add_argument("--reference", action="append", default=[],
                    help="参照技能库目录（可多次，先命中优先），如 <技能安装位>")
    ap.add_argument("--workdir", default=None, help="解压工作目录")
    ap.add_argument("--seal", default=None, help="封存包输出路径（.zip）")
    ap.add_argument("--smoke", action="store_true", help="合成样例自检")
    a = ap.parse_args()

    if a.smoke:
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            inner = t / "inner.zip"
            with zipfile.ZipFile(inner, "w") as z:
                z.writestr("SKILL.md", "name: demo\n")
            outer = t / "outer.zip"
            with zipfile.ZipFile(outer, "w") as z:
                z.write(inner, "demo-skill.zip")
            work = t / "work"
            log = unpack_recursive(outer, work)
            assert any(r["pkg"] == "demo-skill.zip" and r["status"] == "ok" and r["files"] == 1 for r in log), log
            print("SMOKE OK:", json.dumps(log, ensure_ascii=False))
        return 0

    if not a.source:
        ap.error("缺少源包路径（或用 --smoke）")
    src = Path(a.source)
    today = date.today().isoformat()
    work = Path(a.workdir) if a.workdir else Path(f"./batch_run_{today}")
    refs = [Path(r) for r in a.reference]

    # 1 解压
    log = unpack_recursive(src, work / "_outer")
    subzips = sorted((work / "_outer").glob("*.zip"))
    extract_root = work / "extracted"
    extract_root.mkdir(exist_ok=True)
    detail = []
    for zp in subzips:
        before = len(detail)
        unpack_recursive(zp, extract_root / zp.stem, log=detail)
    ok = sum(1 for r in detail if r["status"] == "ok" and r["files"] >= 0)

    # 2 审计
    rows = audit(extract_root, refs) if refs else []

    # 3 登记表
    reg = [f"# 简化归档登记表（{today}）", "",
           f"- 源包：{src}", f"- 子包解压成功：{ok}/{len(subzips)}（CRC 校验）", "",
           "| 技能包 | 文件数 | 现装版位置 | 结论 |", "|---|---|---|---|"]
    for r in rows:
        reg.append(f"| {r['skill']} | {r['files']} | {r['ref'] or '—'} | {r['verdict']} |")
    registry_md = "\n".join(reg)

    # 4 封存
    if a.seal:
        readme = (f"# 技能旧包封存档案（{today}）\n\n"
                  f"来源：{src.name}，共 {len(subzips)} 个子包。\n"
                  f"内容：原始子包 zip + 本 README + registry.md（简化归档登记表）。\n"
                  f"结论：旧包内容已经哈希审计，现装版覆盖情况见 registry.md；本档案仅作历史留存。\n")
        seal(subzips, Path(a.seal), registry_md, readme)

    print(registry_md)
    if a.seal:
        print(f"\n封存包: {a.seal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
