import json,os,glob,subprocess
reg='<注册处>'
fails=[]
old=glob.glob(f'{reg}/案头事项逐项深研_v1.0*')
if old: fails.append(f'旧名残留:{old}')
t=open(f'{reg}/案头事项逐项深研_v1.1_20260903.md',encoding='utf-8').read()
for k in ['10.8 万','085500','2.8 万/年','战略主线','取证清单','排除']:
    if k not in t: fails.append(f'缺:{k}')
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','346'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor346')
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
