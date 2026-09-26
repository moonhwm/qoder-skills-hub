#!/usr/bin/env python3
# redundancy_scan.py v1.0.0 — 技能/注册处冗余重复扫描器（条款级复写检测）
# 用法: python3 redundancy_scan.py [技能目录1] [技能目录2] ...
#   默认扫描 <技能安装位> 治理六件 + 注册处 *.md
# 输出: 关键条款（写类例外/红线/自我优化/信息充分性/授权法典）在文件间的复写分布与漂移嫌疑
import re, sys, os, glob

CLAUSES = {
    "写类例外": r"写类例外",
    "红线": r"红线",
    "自我优化(I9)": r"自我优化条款（I9|§12 自我优化第一要义",
    "信息充分性": r"信息充分性条款",
    "授权法典": r"授权法典",
    "引用不复制": r"引用不复制",
}

def scan(paths):
    hits = {}
    for p in paths:
        for f in glob.glob(os.path.join(p, "**/*.md"), recursive=True):
            try:
                t = open(f, encoding="utf-8").read()
            except OSError:
                continue
            for name, pat in CLAUSES.items():
                for m in re.finditer(pat, t):
                    line_start = t.rfind("\n", 0, m.start()) + 1
                    line = t[line_start:t.find("\n", m.start())][:80]
                    hits.setdefault(name, {}).setdefault(f, []).append(line)
    return hits

def main():
    paths = sys.argv[1:] or [
        "<技能安装位>/<自主推进件>",
        "<技能安装位>/<统调件>",
        "<技能安装位>/plugin-datasource-ops",
        "<技能安装位>/「额度守护件」",
        "<技能安装位>/<重装件>",
        "<技能安装位>/consignment-intake-ops",
        "<注册处>",
    ]
    hits = scan(paths)
    drift_flag = 0
    for name, files in hits.items():
        full_text_files = [f for f, lines in files.items() if any(len(l) > 60 for l in lines)]
        print(f"## {name}: {len(files)} 文件命中")
        for f, lines in files.items():
            print(f"   {f} ×{len(lines)}")
        if len(full_text_files) >= 2:
            # 简化漂移嫌疑：多文件含长条款行=复写级（应改单源引用）
            print(f"   ⚠ 复写级嫌疑 {len(full_text_files)} 处——母本留全文、其余应改一句指针（规范 I8）")
            drift_flag = 1
    print(f"\n复写级嫌疑条款数: {drift_flag}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
