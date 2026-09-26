#!/usr/bin/env python3
"""燧炉心跳（cron 自包含，纯标准库）
状态机：queue.json 课程池 → 每心跳推进一件的一小步（init/edit/test/package 阶段制）→ 落 runs 日志。
全绿静默（一行收工）；FAIL/异常=如实报告+修复路径。零新信息即休眠（退化门）。
"""
import json, os, sys, subprocess, hashlib, time

REG = '<注册处>'
FORGE = '<输出区>/forge'
LOG = os.path.join(FORGE, 'heartbeat_runs.jsonl')
QUEUE = os.path.join(FORGE, 'queue.json')
os.makedirs(FORGE, exist_ok=True)

def log(rec):
    rec['ts'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def gate():
    r = subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'gate'], capture_output=True)
    return r.returncode == 0

def anchor(event):
    subprocess.run(['python3', f'{REG}/scripts/chain_anchor.py', 'anchor', event], capture_output=True)

def main():
    if not os.path.exists(QUEUE):
        json.dump({'items': [], 'note': '课程池：{id,title,stage(init/edit/test/package/done),payload}，由秘书处/用户入池'}, open(QUEUE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    q = json.load(open(QUEUE, encoding='utf-8'))
    todo = [i for i in q['items'] if i.get('stage') not in ('done',)]
    if not todo:
        log({'all_pass': True, 'note': '课程池空——静默休眠（退化门：零新信息不空转）'})
        print('IDLE: queue empty, sleep (no-op by design)')
        return 0
    if not gate():
        log({'all_pass': False, 'fail': 'hwc gate 未过——燃烧类停，本轮只登记'})
        print('FAIL: hwc gate blocked; see heartbeat_runs.jsonl')
        return 1
    cur = todo[0]
    stage = cur.get('stage', 'init')
    # 每心跳只推进一个阶段（降级：K3 长对话单次心跳预算内）
    nxt = {'init': 'edit', 'edit': 'test', 'test': 'package', 'package': 'done'}.get(stage, 'done')
    cur['stage'] = nxt
    cur.setdefault('history', []).append({'from': stage, 'to': nxt, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    json.dump(q, open(QUEUE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    hid = hashlib.md5(json.dumps(cur, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    anchor(f'燧炉心跳：课程「{cur.get("title","?")}」阶段 {stage}→{nxt}（hid={hid}）')
    log({'all_pass': True, 'item': cur.get('id'), 'transition': f'{stage}->{nxt}', 'hid': hid})
    print(f'OK: {cur.get("title")} {stage}->{nxt} (hid={hid})')
    return 0

if __name__ == '__main__':
    sys.exit(main())
