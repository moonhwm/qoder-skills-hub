import glob,subprocess
reg='<注册处>'
fails=[]
if glob.glob(f'{reg}/案头事项逐项深研_v1.3*'): fails.append('v1.3残留')
t=open(f'{reg}/案头事项逐项深研_v1.4_20260903.md',encoding='utf-8').read()
for k in ['S1','S5','A1','甲乙丙丁','R1','R3','全案收敛','三取证','不承诺逻辑绝对完备']:
    if k not in t: fails.append(f'缺:{k}')
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','349'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor349')
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
