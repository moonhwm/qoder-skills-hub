#!/usr/bin/env python3
# verifier v4 机检 —— 礼赠池死线批次（2026-09-02）
import os, sys, json, re, subprocess

REG = '<注册处>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

P0 = f'{REG}/退休工程P0呈批三卡_v1.0_20260902.md'
PR = f'{REG}/用量参数重估呈批件_日闸与月软警_v1.0_20260902.md'
WO = f'{REG}/GLM旧号礼赠池死线燃烧工单_v1.0_20260902.md'

# E1 三文书落盘且要素齐
t0 = open(P0, encoding='utf-8').read() if os.path.exists(P0) else ''
t1 = open(PR, encoding='utf-8').read() if os.path.exists(PR) else ''
t2 = open(WO, encoding='utf-8').read() if os.path.exists(WO) else ''
ok('E1a P0三卡要素', all(k in t0 for k in ['追认信封', '准M4', '建心跳', '死守级', 'Q1']))
ok('E1b 参数件要素', all(k in t1 for k in ['事由', '备份', '报告', '回滚日闸', '¥50', '准A/B/C/D']))
ok('E1c 工单要素', all(k in t2 for k in ['03:30', 'W1', 'W2', 'W3', 'L3_DRILL_ACK', '回执']))

# E2 cron 卡 lint PASS（现场重新运行以留存记录）
r = subprocess.run(['python3', '<技能安装位>/cron-task-forge/scripts/card_linter.py',
                    '--name', '退休工程·L3每日巡检心跳', '--cron', '30 5 * * *', '/tmp/l3_card.txt'],
                   capture_output=True, text=True)
ok('E2 cron卡lint', '"verdict": "PASS"' in r.stdout, r.stdout.strip()[:60])

# E3 无明文凭证（七项＋vault 密钥前缀）
SECRETS = ['REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED20']  # 本轮新增：external_seat.json api_key 前缀（内部输出误露前20字符，禁入文书）
hits = []
for tp in (P0, PR, WO):
    if not os.path.exists(tp): continue
    c = open(tp, encoding='utf-8', errors='ignore').read()
    for s in SECRETS:
        if s in c: hits.append(f'{os.path.basename(tp)}:{s[:6]}…')
ok('E3 零明文凭证', not hits, f'hits={hits}')

# E4 数字一致（台账实证 vs 文书）
import subprocess as sp
rep = sp.run(['python3', f'{REG}/scripts/hwc_usage.py', 'report'], capture_output=True, text=True).stdout
ok('E4a MaaS全史¥0.37', '¥0.3719' in rep and '¥0.37' in t1, rep.split(chr(10))[0])
ok('E4b Kimi实证引用', '¥10,355.41' in t1 and '¥299.59' in t1)

# E5 零越权
src = open(f'{REG}/scripts/hwc_usage.py', encoding='utf-8').read()
ok('E5a 参数未动', 'DAILY_CAP = 50.0' in src and 'MONTHLY_SOFT_CAP = 800.0' in src)
crons = json.load(open(f'{REG}/计时器任务台账.json', encoding='utf-8'))['tasks']
ok('E5b 未新增cron', len(crons) == 13, f'tasks={len(crons)}')
ok('E5c 无心跳注册记录', not any('巡检心跳' in json.dumps(t, ensure_ascii=False) and t.get('status') == 'active' for t in crons))

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
