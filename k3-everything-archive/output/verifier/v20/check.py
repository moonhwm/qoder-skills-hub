import glob,json,subprocess
reg='<注册处>'
fails=[]
if glob.glob(f'{reg}/案头事项逐项深研_v1.4*'): fails.append('v1.4残留')
t=open(f'{reg}/案头事项逐项深研_v1.5_20260903.md',encoding='utf-8').read()
for k in ['同等法律效力','南网北京研究院','60 人','撞期警告','基本不被认可']:
    if k not in t: fails.append(f'缺:{k}')
d=json.load(open(f'{reg}/逃逸登记册.json',encoding='utf-8'))
e24=[e for e in d['entries'] if e.get('id')==24]
assert e24 and e24[0]['bad']==1, 'escape24'
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','350'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor350')
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
