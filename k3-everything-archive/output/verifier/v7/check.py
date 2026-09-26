#!/usr/bin/env python3
# verifier v7 机检 —— 撞墙处置批次（2026-09-02）
import os, sys, json

REG = '<注册处>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

# H1 Q2 熔断
d = json.load(open(f'{REG}/额度状态台账.json', encoding='utf-8'))
ok('H1 Q2熔断登记', d.get('tier') == 'Q2' and d.get('current_level') == 'Q2'
   and any('撞墙' in json.dumps(h, ensure_ascii=False) for h in d.get('history', [])),
   f"tier={d.get('tier')} history={len(d.get('history', []))}")

# H2 计时器标注
d2 = json.load(open(f'{REG}/计时器任务台账.json', encoding='utf-8'))
blob = json.dumps(d2, ensure_ascii=False)
ok('H2a 东富龙撞墙标注', '触发回执待核' in blob and '撞墙' in blob)
ok('H2b 蜂群冻结标注', 'Q2熔断期冻结' in blob)

# H3 写回队列第9次
q = open('<上传区>/skill-dist-20260831/写回队列.md', encoding='utf-8').read()
ok('H3 第9次登记', '第 9 次登记' in q and '63' in q and '母本' in q)

# H4 台账可解析
bad = []
for fn in ('交割台账.json', '计时器任务台账.json', '额度状态台账.json', '逃逸登记册.json'):
    try: json.load(open(f'{REG}/{fn}', encoding='utf-8'))
    except Exception: bad.append(fn)
ok('H4 台账可解析', not bad, f'bad={bad}')

# H5 零燃烧零越权
src = open(f'{REG}/scripts/hwc_usage.py', encoding='utf-8').read()
ledger_lines = sum(1 for _ in open(f'{REG}/蜂群消耗台账.jsonl', encoding='utf-8'))
SECRETS = ['REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED20']
hits = []
for tp in (f'{REG}/额度状态台账.json', f'{REG}/计时器任务台账.json',
           '<上传区>/skill-dist-20260831/写回队列.md'):
    c = open(tp, encoding='utf-8', errors='ignore').read()
    for s in SECRETS:
        if s in c: hits.append(os.path.basename(tp))
ok('H5a 参数未动', 'DAILY_CAP = 50.0' in src and 'MONTHLY_SOFT_CAP = 800.0' in src)
ok('H5b 燃烧台账零新增', ledger_lines == 21, f'lines={ledger_lines}')
ok('H5c 零明文凭证', not hits, f'hits={hits}')

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
