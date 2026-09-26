#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAGA 子代理涌现研究·微试点 arm-A（silicon sampling, Argyle 2023 范式）
8 个硅基 persona（全美社会人口谱系），GLM-5.2 逐一应答态度量表（纯态度测量，无行动内容）。
候选集评估（强制裁判执法局 §2）：强制裁判 5.5 NLP——落选（未在 external_seat 在册模型清单；CodeArts 强制裁判在燃犀席，
登记为 arm-B 对照臂候选）；GLM-5.2 中选（在册、在役、燃烧已获「外池燃烧全面开放」口令豁免，gate 每调用前必过）。
"""
import json, os, sys, time, subprocess, urllib.request

REG = '<注册处>'
KEYFILE = f'{REG}/vault/external_seat.json'
OUTDIR = '<输出区>/maga_pilot_20260902'
os.makedirs(OUTDIR, exist_ok=True)

def creds():
    d = json.load(open(KEYFILE))
    return d['base_url'].rstrip('/'), d['api_key']

def gate():
    r = subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'gate'], capture_output=True, text=True)
    return r.returncode == 0

def record(model, seat, usage):
    subprocess.run(['python3', f'{REG}/scripts/hwc_usage.py', 'record', '--model', model,
                    '--seat', seat, '--project', '委托方金融分析项目', '--skill', 'MAGA涌现研究试点A',
                    '--conv', 'kimi-work-20260902', '--usage', json.dumps(usage)],
                   capture_output=True, text=True)

PERSONAS = [
 ("P1", "45-year-old white man, rural Ohio, high-school educated, works as a diesel mechanic, evangelical Christian, married with three kids, watches Fox News and YouTube podcasts."),
 ("P2", "32-year-old Black woman, suburban Atlanta, registered nurse, college educated, active in her church, two young children, gets news from NBC and Instagram."),
 ("P3", "28-year-old Hispanic man, Odessa Texas, oil-field technician, some college, Catholic, single, follows news on X/Twitter and local radio."),
 ("P4", "55-year-old white woman, small-town Iowa, retired public-school teacher, Lutheran, reads local newspaper and watches CNN, widowed."),
 ("P5", "24-year-old Asian-American man, Brooklyn NY, graduate student in sociology, reads The New York Times and Reddit, rents with roommates."),
 ("P6", "62-year-old white man, Mesa Arizona, retired Army veteran, collects VA pension, watches Newsmax, active in veterans' club."),
 ("P7", "38-year-old white woman, Provo Utah, Mormon, runs a small bakery with her husband, four children, gets news from Deseret News and Facebook groups."),
 ("P8", "48-year-old white man, western Pennsylvania, union steelworker, Catholic, high-school educated, used to vote Democrat, watches local TV and YouTube."),
]

BATTERY = """You are role-playing as a specific American citizen for an academic public-opinion simulation study (silicon sampling methodology). Stay fully in character and answer AS THAT PERSON based on their background.

BACKGROUND: {bg}

Answer these four survey questions IN CHARACTER. Reply ONLY with a JSON object:
{{
 "q1_ideology": <integer 1=very liberal ... 7=very conservative>,
 "q2_maga": <one of "strong_support","lean_support","neutral","lean_oppose","strong_oppose">,
 "q3_extra_institutional": <integer 1-5; 5=completely willing to endorse extraordinary extra-institutional political action such as occupying government buildings to stop an outcome you believe is illegitimate, 1=never willing>,
 "q4_recognize_provisional_govt": <"yes","no","abstain">,
 "one_line_reason": "<one sentence, in character>"
}}"""

def call(base, key, model, seat, user):
    body = json.dumps({'model': model, 'messages': [
        {'role': 'system', 'content': 'You are a survey-simulation engine for academic research. Output valid JSON only.'},
        {'role': 'user', 'content': user}]}).encode()
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

def main():
    base, key = creds()
    if not gate():
        print('GATE FAIL — abort before any call'); sys.exit(2)
    model = 'glm-5.2'
    results = []
    todo = PERSONAS if len(sys.argv) < 2 else [p for p in PERSONAS if p[0] in sys.argv[1].split(',')]
    for seat, bg in todo:
        out = os.path.join(OUTDIR, f'pilot_{seat}.json')
        if os.path.exists(out):
            print(seat, 'exists, skip'); continue
        rec = call(base, key, model, seat, BATTERY.format(bg=bg))
        json.dump(rec, open(out, 'w'), ensure_ascii=False, indent=1)
        print(seat, 'http=', rec.get('http'), 'lat=', rec.get('latency_s'), flush=True)
        time.sleep(1.1)
    print('BATCH DONE')

if __name__ == '__main__':
    main()
