#!/usr/bin/env python3
# verifier v5 机检 —— L3联合国模式试点（2026-09-02）
import os, sys, json

REG = '<注册处>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

DP = f'{REG}/L3试点_联合国模式决议草案与议事设计_v1.0_20260902.md'
t = open(DP, encoding='utf-8').read() if os.path.exists(DP) else ''

ok('F1 草案要素', all(k in t for k in ['S/2026/L3-01', 'R1', 'R2', 'R3', '无常任反对', '附卷（不表决）', '非满员试点']))
ok('F2 规程并轨', all(k in t for k in ['弃权', '分部分表决', '平票=否决', '记录表决', '表决中不打断' if '表决中不打断' in t else '表决进行中']))
ok('F3 权力不动', all(k in t for k in ['首席常任', '终审', '签收 L3', '用户专决']))

LP = f'{REG}/表决记录册_S2026L3-01.jsonl'
rows = []
if os.path.exists(LP):
    for ln in open(LP, encoding='utf-8'):
        ln = ln.strip()
        if ln:
            try: rows.append(json.loads(ln))
            except Exception: rows.append(None)
ok('F4a 记录册可解析', rows and all(r for r in rows), f'rows={len(rows)}')
ok('F4b 仅创刊行无伪造票', len(rows) == 1 and rows[0].get('type') == '创刊登记' and '票型' not in json.dumps(rows, ensure_ascii=False))

SECRETS = ['REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED20']
hits = []
for tp in (DP, LP):
    if not os.path.exists(tp): continue
    c = open(tp, encoding='utf-8', errors='ignore').read()
    for s in SECRETS:
        if s in c: hits.append(os.path.basename(tp))
ok('F5a 零明文凭证', not hits, f'hits={hits}')
src = open(f'{REG}/scripts/hwc_usage.py', encoding='utf-8').read()
crons = json.load(open(f'{REG}/计时器任务台账.json', encoding='utf-8'))['tasks']
ok('F5b 零越权', 'DAILY_CAP = 50.0' in src and len(crons) == 13, f'tasks={len(crons)}')

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
