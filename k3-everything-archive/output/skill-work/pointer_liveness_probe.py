#!/usr/bin/env python3
"""pointer_liveness_probe.py v1.0 — 指针活性探针
扫描 markdown 产物中的本地路径指针，核验文件存在性，输出死指针清单。
来源：《减回忆依赖机制有效性评估_v1.0》增量建议①（ROI 最高项）。
用法: python3 pointer_liveness_probe.py [根目录...]  退出码 0=全活 1=有死指针
"""
import re, sys
from pathlib import Path

ROOTS = sys.argv[1:] or ["<注册处>", "<上传区>/委托方金融分析项目"]
SEARCH_BASES = [Path("<上传区>"), Path("<输出区>"), Path("/"), Path("<上传区>/委托方金融分析项目"), Path("<输出区>/skill-work")]
# 匹配形如 xxx/yyy.md / 05_迭代日志/xxx.json / registry/yyy.md 等相对或绝对路径
PAT = re.compile(r"[\w\u4e00-\u9fff][\w\u4e00-\u9fff\-_.]*/[\w\u4e00-\u9fff\-_./()]+?\.(?:md|json|py|csv|db|skill|docx)")
SKIP = ("http", "sandbox:")

def resolve(ptr):
    p = Path(ptr)
    if p.is_absolute() and p.exists():
        return True
    for b in SEARCH_BASES:
        if (b / ptr).exists():
            return True
    # 常见别名: registry/ 前缀
    if ptr.startswith("registry/") and (Path("<注册处>") / ptr[9:]).exists():
        return True
    return False

dead, total = [], 0
for root in ROOTS:
    for f in Path(root).rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in PAT.finditer(text):
            ptr = m.group(0)
            if any(s in ptr for s in SKIP):
                continue
            total += 1
            if not resolve(ptr):
                dead.append((str(f), ptr))
print(f"扫描指针 {total} 个，死指针 {len(dead)} 个")
for f, ptr in dead:
    print(f"DEAD  {f}  ->  {ptr}")
sys.exit(1 if dead else 0)
