#!/usr/bin/env python3
# verifier v1 机检脚本 — 已停用项目
import re, os, sys, json, subprocess

REG='<注册处>'
OUT='<输出区>'
fails=[]

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

# V1 保皇党报告
p=f'{REG}/保皇党审计报告_v1.0_20260902.md'
t=open(p,encoding='utf-8').read() if os.path.exists(p) else ''
missing=[f'A{i}' for i in range(1,16) if f'A{i}' not in t]
ok('V1a A1-A15全覆盖', not missing, f'missing={missing}')
ok('V1b 三分类齐', all(k in t for k in ['死守级','可改造级','可委托级']))

# V2 技能隔离报告（后续轮产出，存在才检）
p2=f'{REG}/技能重叠隔离与卫生化报告_v1.0_20260902.md'
if os.path.exists(p2):
    t2=open(p2,encoding='utf-8').read()
    names=['data-viz-gen','gitlab-cli-guide','humanizer-zh','k8s-cluster-ops',
           'rust-browser-pilot','seo-copywriting-guide','software-testing-guide','web-security-audit']
    miss=[n for n in names if n not in t2]
    ok('V2a 8交集覆盖', not miss, f'missing={miss}')
    ok('V2b humanizer三变体', all(k in t2 for k in ['humanizer','humanizer-zh-by-guizang']))
else:
    print('SKIP V2 报告未产出')

# V3 Loop蓝图
p3=f'{REG}/Loop自动化蓝图_v1.0_20260902.md'
if os.path.exists(p3):
    t3=open(p3,encoding='utf-8').read()
    ks=['Automations','Worktrees','Skills','MCP','Sub-agents','Memory','Maker','Checker','硬门禁','空转']
    miss=[k for k in ks if k not in t3]
    ok('V3 蓝图要素', not miss, f'missing={miss}')
else:
    print('SKIP V3 蓝图未产出')

# V4 学术固化
p4=f'{REG}/Loop工程学术固化报告_v1.0_20260902.md'
if os.path.exists(p4):
    t4=open(p4,encoding='utf-8').read()
    ids=re.findall(r'(?:arXiv[::]?\s*)?(\d{4}\.\d{4,5})', t4)
    ok('V4 ≥5篇arXiv', len(set(ids))>=5, f'ids={sorted(set(ids))[:8]}')
else:
    print('SKIP V4 未产出')

# V5 用量三件套
p5=f'{REG}/用量参数变更三件套_日闸_v1.0_20260902.md'
if os.path.exists(p5):
    t5=open(p5,encoding='utf-8').read()
    ok('V5 三件套字段', all(k in t5 for k in ['事由','备份','报告','¥5','新闸']))
else:
    print('SKIP V5 未产出')

# V8 明文凭证零泄漏（对应 registry 20260902 新文档 + output 交付）
SECRETS=['REDACTED_LEGACY','REDACTED_LEGACY','REDACTED_LEGACY',
         'REDACTED_LEGACY','REDACTED_LEGACY','REDACTED_LEGACY','REDACTED_LEGACY']
hits=[]
targets=[]
for fn in os.listdir(REG):
    if fn.endswith('_20260902.md'): targets.append(os.path.join(REG,fn))
for root,_,fs in os.walk(OUT):
    if 'verifier' in root: continue
    for fn in fs:
        if fn.endswith(('.md','.json','.py','.txt')): targets.append(os.path.join(root,fn))
for tp in targets:
    try: c=open(tp,encoding='utf-8',errors='ignore').read()
    except: continue
    for s in SECRETS:
        if s in c: hits.append(f'{os.path.basename(tp)}:{s[:6]}...')
ok('V8 零明文凭证', not hits, f'hits={hits}')

print('---')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
