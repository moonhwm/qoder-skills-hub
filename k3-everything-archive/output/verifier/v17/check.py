import glob,subprocess
reg='<注册处>'
fails=[]
if glob.glob(f'{reg}/案头事项逐项深研_v1.1*'): fails.append('v1.1残留')
t=open(f'{reg}/案头事项逐项深研_v1.2_20260903.md',encoding='utf-8').read()
for k in ['单证','同等学力**申请**','仅限法律、会计、出版专博','电子信息：30000元/年','D1','A2','双主线','立法排除']:
    if k not in t: fails.append(f'缺:{k}')
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','347'],capture_output=True,text=True)
if 'PASS' not in v.stdout: fails.append('anchor347')
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
