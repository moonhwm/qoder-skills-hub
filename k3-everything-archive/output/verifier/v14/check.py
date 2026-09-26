import json,os,subprocess,re
reg='<注册处>'
fails=[]
n=len([d for d in os.listdir('<技能安装位>') if os.path.isdir(f'<技能安装位>/{d}')])
print('install count:',n)
if not os.path.isdir('<技能安装位>/k3-channel-ops'): fails.append('channel-ops missing')
r=subprocess.run(['find','/','-maxdepth','6','-iname','*k3-forge*','-not','-path','/proc/*','-not','-path','/sys/*'],capture_output=True,text=True)
found=[l for l in r.stdout.splitlines() if 'forge-catalog' in l.lower()]
print('forge-catalog found:',found)
if found: fails.append('forge-catalog unexpectedly exists')
d=json.load(open(f'{reg}/逃逸登记册.json',encoding='utf-8'))
e23=[e for e in d['entries'] if e.get('id')==23]
assert e23 and '虚报' in e23[0]['类型'], 'escape23'
v=subprocess.run(['python3',f'{reg}/scripts/chain_anchor.py','--verify','344'],capture_output=True,text=True)
print(v.stdout.strip().splitlines()[-1])
if 'PASS' not in v.stdout: fails.append('anchor344')
txt=open(f'{reg}/skill-creator-learning/cards/cardlint.log',encoding='utf-8').read() if os.path.exists(f'{reg}/skill-creator-learning/cards/cardlint.log') else ''
print('FAILS:',fails); raise SystemExit(1 if fails else 0)
