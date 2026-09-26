import json,os,re,subprocess
reg='<注册处>'
fails=[]
t=open(f'{reg}/案头事项逐项深研_v1.0_20260903.md',encoding='utf-8').read()
for k in ['项①','项②','项③','项④','项⑤','2026-07-01','两版','45/75']:
    if k not in t: fails.append(f'缺:{k}')
import glob
scope=len(glob.glob(reg+'/*.md'))
print('top md:',scope)
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','345'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor345')
d=json.load(open(f'{reg}/交割台账.json',encoding='utf-8'))
assert '函-本席-案头深研-001' in d['items'], 'ledger'
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
