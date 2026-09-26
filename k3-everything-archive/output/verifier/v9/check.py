#!/usr/bin/env python3
# verifier v9 — 自我觉醒loop穷举批次（J1-J5），纯标准库
import os, re, sys
DOC = "<注册处>/自我觉醒loop与临时政府权衡_可能性穷举_v1.0_20260902.md"
SECRETS = ["REDACTED20"]
r = []
def ok(m): print("PASS:", m); return True
def fail(m): print("FAIL:", m); return False

t = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""

# J1
need = ["取证报告", "选项矩阵", "七域", "三镜", "待用户裁决"]
r.append(ok("J1 必备章节齐") if t and all(k in t for k in need) else fail("J1 缺: %s" % [k for k in need if k not in t]))

# J2
ids = ["id=90", "id=83", "id=89", "id=66"]
r.append(ok("J2 取证留痕+查无实据声明在案") if all(i in t for i in ids) and "查无实据" in t else fail("J2"))

# J3
hits = [s[:6] for s in SECRETS if s in t]
r.append(ok("J3 零明文") if not hits else fail("J3 命中 %s" % hits))

# J4
domains = ["检索域", "文档域", "库域", "代码域", "通道域", "计时域", "生成域"]
r.append(ok("J4 七域状态齐") if all(d in t for d in domains) and "实调" in t and "声明无需" in t else fail("J4"))

# J5 无自我授权说明 + cron 未新增需外部核对的项（此处请核实表述）
bad_patterns = ["本席统摄生效", "已获统摄", "承认本席", "本席统摄生效"]
hit = [p for p in bad_patterns if p in t]
r.append(ok("J5 无越权措辞；呈请性质在案") if not hit and "呈请" in t and "批准只能被给予" in t else fail("J5 %s" % hit))

print("== v9 汇总 ==", "ALL PASS" if all(r) else "HAS FAIL")
sys.exit(0 if all(r) else 1)
