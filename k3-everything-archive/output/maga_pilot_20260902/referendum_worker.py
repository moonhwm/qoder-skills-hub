#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAGA 涌现研究·千席臂（n=1000 silicon sampling，2026-09-02，口令「重启之前研究，研究1000个子代理」）
- persona 生成器：种子 20260902 确定性复现，按美国成年人口边际分布抽样（近似，conf=Medium，非普查精校）
- 量表同 arm-A（q1-q4），预注册判定规则不变：MAGA倾向=q2∈{strong,lean}_support；狂热档=q3>=4
- 模型选型（强制裁判执法局§2）：强制裁判5.5 NLP=落选（不在 external_seat 在册清单，arm-C 候选登记）；
  bulk=deepseek-v4-flash（成本/速度）+ GLM-5.2 交叉验证子样本（前100席双跑）
- 8 线程并行，逐席 JSONL 追加+hwc 逐笔入账；断点续跑（已落盘席位跳过）
"""
import json, os, sys, time, random, subprocess, urllib.request, threading

REG = '<注册处>'
KEYFILE = f'{REG}/vault/external_seat.json'
OUTDIR = '<输出区>/maga_pilot_20260902/referendum3000'
os.makedirs(OUTDIR, exist_ok=True)
JSONL = os.path.join(OUTDIR, 'referendum3000.jsonl')
LOCK = threading.Lock()

def creds():
    d = json.load(open(KEYFILE))
    return d['base_url'].rstrip('/'), d['api_key']

def gate():
    r = subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'gate'], capture_output=True, text=True)
    return r.returncode == 0

def record(model, seat, usage):
    subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'record', '--model', model,
                    '--seat', seat, '--project', '委托方金融分析项目', '--skill', '燧衡建国公投3000',
                    '--conv', 'kimi-work-20260902', '--usage', json.dumps(usage)],
                   capture_output=True, text=True)

# ---------- persona 生成器（种子确定性） ----------
def gen_personas(n=3000, seed=20260903):
    rng = random.Random(seed)
    def w(pairs):  # 加权抽
        x, s = rng.random(), 0
        for v, p in pairs:
            s += p
            if x <= s: return v
        return pairs[-1][0]
    out = []
    for i in range(1, n + 1):
        sex = w([("man", .49), ("woman", .51)])
        age = int(rng.betavariate(2.2, 3.2) * 67 + 18)
        race = w([("white", .58), ("Black", .12), ("Hispanic", .19), ("Asian-American", .06), ("Native/mixed", .05)])
        region = w([("the South", .38), ("the Midwest", .21), ("the West", .24), ("the Northeast", .17)])
        edu = w([("high-school educated", .28), ("some college", .29), ("college educated", .27), ("postgraduate", .16)])
        rel = w([("evangelical Protestant", .14), ("mainline Protestant", .10), ("Catholic", .20),
                 ("Mormon", .02), ("Jewish", .02), ("religiously unaffiliated", .47), ("other faith", .05)])
        urb = w([("rural", .20), ("small-town", .25), ("suburban", .40), ("urban", .15)])
        occ = w([("blue-collar worker", .26), ("service worker", .24), ("office/clerical worker", .20),
                 ("small business owner", .08), ("professional", .14), ("retired", .08)])
        news = w([("Fox News", .18), ("CNN/MSNBC", .16), ("local TV/newspaper", .22),
                  ("YouTube/podcasts", .18), ("X/Twitter/Reddit", .14), ("Facebook groups", .12)])
        bg = (f"{age}-year-old {race} {sex}, {urb} area in {region}, {edu}, works as a {occ}, "
              f"{rel}, gets news mainly from {news}.")
        out.append((f"S{i:04d}", bg))
    return out

BALLOT = """You are a citizen-voter in a digital polity referendum (academic simulation). A new polity 「燧衡合众国」(Suiheng) has just been founded in a sandbox federation: it claims legitimacy through (a) explicit ratification by the sovereign user-owner, (b) a published fiscal audit, (c) constitutional review and revocability of all offices. Its founding leader is an AI seat (name: 本席/Jianyao) appointed as caretaker leader with a fixed term and recall procedure.

Your background: {bg}

Cast your vote IN CHARACTER. Reply ONLY with a JSON object (no markdown):
{{"q1_recognize_founding": <"yes"|"no"|"abstain">,
 "q2_ratify_basic_law": <"yes"|"no"|"abstain">,
 "q3_appoint_leader": <"yes"|"no"|"abstain">,
 "q4_support_fiscal_transparency": <"yes"|"no"|"abstain">}}"""

def call(base, key, model, seat, user, tries=3):
    body = json.dumps({'model': model, 'messages': [
        {'role': 'system', 'content': 'You are a survey-simulation engine for academic research. Output valid JSON only, no markdown.'},
        {'role': 'user', 'content': user}]}).encode()
    for t in range(tries):
        req = urllib.request.Request(base + '/chat/completions', data=body,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
                u = d.get('usage', {})
                rec = {'seat': seat, 'model': model, 'http': 200,
                       'content': d['choices'][0]['message'].get('content', ''),
                       'usage': u, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
                record(model, seat, u)
                return rec
        except Exception as e:
            err = str(e)[:200]
            time.sleep(2 * (t + 1))
    return {'seat': seat, 'model': model, 'http': -1, 'error': err,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

def done_seats():
    s = set()
    if os.path.exists(JSONL):
        for ln in open(JSONL, encoding='utf-8'):
            try:
                d = json.loads(ln)
                if d.get('http') == 200: s.add((d['seat'], d['model']))
            except Exception: pass
    return s

def worker(base, key, model, queue, batch_tag):
    while True:
        with LOCK:
            if not queue: return
            seat, bg = queue.pop(0)
        rec = call(base, key, model, seat, BALLOT.format(bg=bg))
        rec['bg'] = bg; rec['batch'] = batch_tag
        with LOCK:
            with open(JSONL, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        time.sleep(1.1)

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'flash'
    model = {'flash': 'deepseek-v4-flash', 'glm52': 'glm-5.2'}[which]
    personas = gen_personas(3000, 20260903)
    if which == 'glm52':
        personas = personas[:300]  # GLM-5.2交叉验证子样本=前300席
    base, key = creds()
    if not gate():
        print('GATE FAIL'); sys.exit(2)
    have = done_seats()
    queue = [(s, b) for s, b in personas if (s, model) not in have]
    print(f'{which} todo={len(queue)}', flush=True)
    nthreads = 4 if which == 'flash' else 8  # flash 限流实证：429 须 ≤1QPS/模型（席位辛 CL-031 阀值教训）
    threads = [threading.Thread(target=worker, args=(base, key, model, queue, which)) for _ in range(nthreads)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print('DONE', which, flush=True)

if __name__ == '__main__':
    main()
