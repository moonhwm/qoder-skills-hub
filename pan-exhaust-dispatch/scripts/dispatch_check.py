#!/usr/bin/env python3
"""统调矩阵核验器（纯标准库）：检查一份研究产物是否完成『点名清单逐件二选一』与『七域覆盖』。
用法: python3 dispatch_check.py <产物.md> — 产物须含形如 [x] 件名 或 [skip] 件名 的标记行，及『域名:』小节。"""
import re, sys

ROSTER = ["autonomous-advance-ops","omni-exhaust-research-ops","output-verdict-gate","semantic-oncology-ops",
          "quota-guard-ops","plugin-datasource-ops","pangu-enforcement-bureau","coordination-letter",
          "consignment-intake-ops","cron-task-forge","skill-reinstall-ops","skill-refresh-ops",
          "exam-isolation-ops","up-distill-ops","k3-territory-studies"]
DOMAINS = ["检索域","文档域","库域","代码域","通道域","计时域","生成域"]

def main():
    t = open(sys.argv[1], encoding='utf-8').read()
    fails = []
    for r in ROSTER:
        if not re.search(rf'\[(x|skip)\]\s*{re.escape(r)}', t):
            fails.append(f'清单件未二选一: {r}')
    for d in DOMAINS:
        if not re.search(rf'{d}[:：]', t):
            fails.append(f'七域缺声明: {d}')
    if '查无实据' not in t and '证据' not in t:
        fails.append('缺证据/查无实据标注')
    print('FAILS:', fails if fails else '无——统调矩阵+七域核验全绿')
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
