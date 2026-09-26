#!/usr/bin/env python3
"""一拖十覆盖核验：扫产物目录，对每件产物检查 (a) 存在 (b) 非空 (c) 与底册关键数字一致性抽查。
用法: python3 deliverables_check.py <产物目录> [底册md]  — 全绿 exit 0，缺件/漂移 exit 1。"""
import os, re, sys

EXPECTED = ['项目说明', '技术方案', '应用证明', '简讯', '论文', '图文说明', 'PPT', '年终总结']

def numbers(text):
    return set(re.findall(r'\d+(?:\.\d+)?', text))

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    base_nums = set()
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        base_nums = numbers(open(sys.argv[2], encoding='utf-8').read())
    fails, report = [], []
    for key in EXPECTED:
        hits = [f for f in os.listdir(d) if key in f and os.path.getsize(os.path.join(d, f)) > 50] if os.path.isdir(d) else []
        if not hits:
            fails.append(f'缺件或非空不足: {key}')
        else:
            report.append(f'OK {key}: {hits[0]}')
            if base_nums:
                drift = numbers(open(os.path.join(d, hits[0]), encoding='utf-8', errors='ignore').read()) - base_nums
                big = [x for x in drift if float(x) >= 1000]
                if big:
                    fails.append(f'{key} 出现底册外大数字(疑似漂移): {big[:5]}')
    print('\n'.join(report))
    print('FAILS:', fails if fails else '无——十件覆盖核验全绿')
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
