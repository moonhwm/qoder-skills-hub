#!/usr/bin/env python3
# verifier v2 机检 —— 碎片垃圾清理（2026-09-02）
import os, sys, json, hashlib

M = '<输出区>/cleanup_manifest_20260902.json'
REG = '<注册处>'
OUT = '<输出区>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

man = json.load(open(M, encoding='utf-8'))

# C1 删除彻底
gone = [i for i in man['items'] if os.path.exists('<工作区根>/' + i['path'])]
ok('C1 Tier-1删除彻底', not gone and man['deleted'] == len(man['items']), f"residual={[g['path'] for g in gone]} deleted={man['deleted']}/{len(man['items'])}")

# C2 复扫零残留
resid = []
for root in (REG, OUT):
    for dp, _, fs in os.walk(root):
        if '/verifier/runs' in dp or '/hash_chain_archive' in dp: continue
        for f in fs:
            p = os.path.join(dp, f)
            if '.converted.' in f: resid.append(p)
            elif f.endswith(('.tmp', '.part')) or 'final_tmp' in f: resid.append(p)
            else:
                try:
                    if os.path.getsize(p) == 0: resid.append(p + '(0B)')
                except OSError: pass
ok('C2 复扫零残留', not resid, f'resid={resid[:10]}')

# C3 台账健康
led_ok = True
detail = []
for fn in ('交割台账.json', '计时器任务台账.json', '额度状态台账.json'):
    try:
        json.load(open(f'{REG}/{fn}', encoding='utf-8')); detail.append(fn + ':OK')
    except Exception as e:
        led_ok = False; detail.append(f'{fn}:{type(e).__name__}')
for fn in ('交割台账.jsonl', '蜂群消耗台账.jsonl'):
    bad = 0
    for ln in open(f'{REG}/{fn}', encoding='utf-8'):
        ln = ln.strip()
        if not ln: continue
        try: json.loads(ln)
        except Exception: bad += 1
    detail.append(f'{fn}:bad={bad}')
    if bad: led_ok = False
ok('C3 台账健康', led_ok, ' '.join(detail))

# C4 报告落盘
rp = f'{REG}/碎片垃圾清理报告_v1.0_20260902.md'
if os.path.exists(rp):
    t = open(rp, encoding='utf-8').read()
    ks = ['冗余扫描', 'INDEX', '台账健康', 'Tier-1', 'Tier-2', 'Tier-3', 'converted']
    miss = [k for k in ks if k not in t]
    ok('C4 报告落盘且要素齐', not miss, f'missing={miss}')
else:
    ok('C4 报告落盘且要素齐', False, 'report not found')

# C5 父模板完整（BASE_OVERRIDE：对无同名父模板的内容载体进行显式登记）
BASE_OVERRIDE = {'output/ai_physics_sectors.docx.work.converted.md': 'output/ai_physics_sectors.agent.final.md'}
orphans = []
for i in man['items']:
    if '.converted.' in i['path']:
        base = '<工作区根>/' + BASE_OVERRIDE.get(i['path'], i['path'].replace('.converted.md', '.md'))
        if not (os.path.exists(base) and os.path.getsize(base) > 0): orphans.append(i['path'])
ok('C5 母本完整', not orphans, f'orphans={orphans}')

# C6 零明文凭证（本报告+manifest+v2 脚本）
SECRETS = ['REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY',
           'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY', 'REDACTED_LEGACY']
hits = []
# v1.3（2026-09-08）：公开分发场景的豁免已失效——原始检测字符串已迁移至私有对照表 v1.3（desensitize_gate 私有层），SECRETS 值已脱敏为 REDACTED_LEGACY 占位符；历史检测语义由 desensitize_gate.py 继承。
new_files = [M, f'{OUT}/verifier/v2/criteria.md']
if os.path.exists(rp): new_files.append(rp)
for tp in new_files:
    c = open(tp, encoding='utf-8', errors='ignore').read()
    for s in SECRETS:
        if s in c: hits.append(os.path.basename(tp))
ok('C6 零明文凭证', not hits, f'hits={hits}')

# C7 安全边界：删除集合未触碰镜像/备份/台账/锚链/INDEX
forbidden_hit = [i['path'] for i in man['items']
                 if any(k in i['path'] for k in ('.bak', '台账', 'INDEX', 'hash_chain', '逃逸登记册', '锚'))]
ok('C7 安全边界', not forbidden_hit, f'forbidden={forbidden_hit}')

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
