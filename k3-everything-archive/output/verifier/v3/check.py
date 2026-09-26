#!/usr/bin/env python3
# verifier v3 机检 —— INDEX重建+台账小修（2026-09-02）
import os, re, sys, json

REG = '<注册处>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

idx = open(f'{REG}/INDEX.md', encoding='utf-8').read()
actual = {f for f in os.listdir(REG) if os.path.isfile(f'{REG}/{f}')}

# D1a 全覆盖
unindexed = [f for f in actual if f != 'INDEX.md' and f not in idx]
ok('D1a INDEX全覆盖', not unindexed, f'unindexed={unindexed[:8]}')

# D1b 零幽灵（条目行 '- <fname>' 且带扩展名者逐项核验；目录行以/结尾豁免）
ghosts = []
for ln in idx.splitlines():
    m = re.match(r'^- (\S+\.(?:md|json|jsonl|py|txt|docx|skill))\b', ln)
    if m and m.group(1) not in actual:
        ghosts.append(m.group(1))
ok('D1b INDEX零幽灵', not ghosts, f'ghosts={ghosts[:8]}')

# D2 额度台账
d = json.load(open(f'{REG}/额度状态台账.json', encoding='utf-8'))
ok('D2 额度台账schema', d.get('current_level') == 'Q1' and d.get('tier') == 'Q1' and bool(d.get('updated_at')),
   f"current={d.get('current_level')} tier={d.get('tier')}")

# D3 计时器台账
d2 = json.load(open(f'{REG}/计时器任务台账.json', encoding='utf-8'))
noname = [t for t in d2['tasks'] if '任务名' not in t]
ok('D3 计时器格式统一', not noname, f'tasks={len(d2["tasks"])} noname={len(noname)}')

# D4 零明文凭证
SECRETS = ['REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY']
hits = []
for tp in [f'{REG}/INDEX.md', f'{REG}/额度状态台账.json', f'{REG}/计时器任务台账.json']:
    c = open(tp, encoding='utf-8', errors='ignore').read()
    for s in SECRETS:
        if s in c: hits.append(os.path.basename(tp))
ok('D4 零明文凭证', not hits, f'hits={hits}')

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
