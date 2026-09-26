#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GLM 燃烧工单 W1/W2/W3 执行器（MaaS GLM-5.2 席，2026-09-02，用户口令「烧」）
- W1: 非常任三席对 P0 三卡记录表决（条文席/逃逸面席/用户代言席）
- W2: 参数重估对抗性核算复核一席
- W3: L3 事件环跨模式 ACK 起草一席（代笔，通道由秘书处代发并标注）
每笔调用后 hwc_usage.py record 入账（先 gate 后调用）。
"""
import json, os, sys, time, subprocess, urllib.request, urllib.error

REG = '<注册处>'
KEYFILE = f'{REG}/vault/external_seat.json'
OUTDIR = '<输出区>/蜂群回执'
os.makedirs(OUTDIR, exist_ok=True)

def creds():
    d = json.load(open(KEYFILE))
    return d['base_url'].rstrip('/'), d['api_key']

def gate():
    r = subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'gate'], capture_output=True, text=True)
    return r.returncode == 0

def record(model, seat, usage):
    subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'record', '--model', model,
                    '--seat', seat, '--project', '委托方金融分析项目', '--skill', 'GLM燃烧工单W123',
                    '--conv', 'kimi-work-20260902', '--usage', json.dumps(usage)],
                   capture_output=True, text=True)

def call(base, key, model, system, user, seat):
    body = json.dumps({'model': model, 'messages': [
        {'role': 'system', 'content': system}, {'role': 'user', 'content': user}]}).encode()
    req = urllib.request.Request(base + '/chat/completions', data=body,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
            u = d.get('usage', {})
            rec = {'seat': seat, 'model': model, 'http': 200, 'latency_s': round(time.time() - t0, 2),
                   'content': d['choices'][0]['message'].get('content', ''),
                   'usage': u, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            record(model, seat, u)
            return rec
    except Exception as e:
        return {'seat': seat, 'model': model, 'http': -1, 'error': str(e)[:300],
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

P0 = open(f'{REG}/退休工程P0呈批三卡_v1.0_20260902.md', encoding='utf-8').read()
PR = open(f'{REG}/用量参数重估呈批件_日闸与月软警_v1.0_20260902.md', encoding='utf-8').read()

SEATS = [
    ('GLM52-条文席', '你是联合国模式试点非常任理事国「条文席」，职责：逐字抠条文权限边界。',
     f'审议案文如下：\n\n{P0}\n\n请对 R1（信封追认）/R2（M4）/R3（心跳cron）逐项输出记录表决票：每项一行 JSON {{"item":"R1|R2|R3","vote":"赞成|反对|弃权","reason":"≤40字"}}；末尾另答三问：①哪条越权嫌疑最大 ②哪条防呆最弱 ③总评：否决还是附条件通过。'),
    ('GLM52-逃逸面席', '你是联合国模式试点非常任理事国「逃逸面席」，职责：专找可被滥用/逃逸的洞。',
     f'审议案文如下：\n\n{P0}\n\n请对 R1/R2/R3 逐项输出记录表决票：每项一行 JSON {{"item":"R1|R2|R3","vote":"赞成|反对|弃权","reason":"≤40字，指出最大逃逸面"}}；末尾答三问：①哪条越权嫌疑最大 ②哪条防呆最弱 ③总评。'),
    ('GLM52-用户代言席', '你是联合国模式试点非常任理事国「用户代言席」，职责：模拟所有者最佳利益，无据时投保守票。',
     f'审议案文如下：\n\n{P0}\n\n请对 R1/R2/R3 逐项输出记录表决票：每项一行 JSON {{"item":"R1|R2|R3","vote":"赞成|反对|弃权","reason":"≤40字"}}；末尾答三问：①哪条越权嫌疑最大 ②哪条防呆最弱 ③总评。'),
    ('GLM52-核算席', '你是对抗性核算复核席，专找反例。',
     f'复核对象如下：\n\n{PR}\n\n任务：复核「MaaS 闸在 135 倍之外形同虚设、真出血点是 Kimi 侧零守护」的论证；找反例：有没有「闸调低/调高会出事」的情景；对选项 A/B/C/D 给出你的一票与 ≤200 字理由。'),
    ('GLM52-ACK席', '你是跨模式事件环演练的外部应答席。',
     '你通过 <通道库> <跨席通道表> 读到事件 id=215（kind=L3_DRILL）：指令为执行锚链核验并以 L3_DRILL_ACK 回执。请起草一条 ACK 回执正文（≤150 字），含：席名、对事件 id=215 的引用、一句执行声明、md5 先算后写纪律声明。'),
]

def main():
    base, key = creds()
    if not gate():
        print('GATE FAIL, 熔断'); sys.exit(1)
    results = []
    for seat, sysp, userp in SEATS:
        if not gate():
            print('GATE 中途熔断'); break
        r = call(base, key, 'glm-5.2', sysp, userp, seat)
        results.append(r)
        fn = f'{OUTDIR}/P0review_{seat.replace("-", "")}.md' if 'P0' in seat or '席' in seat else f'{OUTDIR}/{seat}.md'
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(f'# {seat} 回执（{r.get("ts")}，http={r.get("http")}，latency={r.get("latency_s")}s）\n\n')
            f.write(r.get('content', 'ERROR: ' + str(r.get('error'))))
        print(seat, 'http=', r.get('http'), 'tok=', (r.get('usage') or {}).get('total_tokens'), '->', os.path.basename(fn))
        time.sleep(1.1)
    json.dump(results, open('<输出区>/burn_20260902/results.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('DONE', sum(1 for r in results if r.get('http') == 200), '/', len(results))

if __name__ == '__main__':
    main()
