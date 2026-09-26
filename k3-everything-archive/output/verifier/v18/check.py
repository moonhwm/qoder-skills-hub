import glob,subprocess
reg='<注册处>'
fails=[]
if glob.glob(f'{reg}/案头事项逐项深研_v1.2*'): fails.append('v1.2残留')
t=open(f'{reg}/案头事项逐项深研_v1.3_20260903.md',encoding='utf-8').read()
for k in ['P1','P2','P3','P4','P5','两个月','4.6','13.5%','4.7%','修正声明','主选系分']:
    if k not in t: fails.append(f'缺:{k}')
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','348'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor348')
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
