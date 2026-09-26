#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""100席蜂群公投演练·单模型队列工人（串行+1QPS+429退避+断点续跑）
用法: python3 drill_worker.py <model_id> <seat_start> <seat_end>   # 席位区间含端点
输出: results_<model>.jsonl 逐条追加
"""
import json, os, sys, time, urllib.request, urllib.error

BASE = None  # 从钥匙文件读
KEYFILE = "<注册处>/vault/external_seat.json"
OUTDIR = "<输出区>/referendum_drill"
MOTION = ("演练案DX-100：是否赞成将蜂群公投通道列为常设演练机制？"
          "请仅输出一行JSON：{\"vote\":\"赞成\"或\"反对\"或\"弃权\",\"reason\":\"≤30字理由\"}，不要输出其他任何内容。")
PERSONAS = ["保守稳健，重视风险", "激进求进，重视效率", "中立务实，看证据",
            "怀疑审慎，常提反例", "乐观建设，倾向支持"]

def load_creds():
    d = json.load(open(KEYFILE))
    return d["base_url"].rstrip("/"), d["api_key"]

def call_model(base, key, model, seat_no):
    persona = PERSONAS[seat_no % len(PERSONAS)]
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": f"你是蜂群公投演练第{seat_no:03d}号席位，投票人格：{persona}。这是压力测试演练，非正式表决。"},
            {"role": "user", "content": MOTION},
        ],
    }).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            lat = time.time() - t0
            d = json.loads(r.read().decode())
            msg = d["choices"][0]["message"].get("content", "")
            u = d.get("usage", {})
            return {"seat": seat_no, "model": model, "http": 200, "latency_s": round(lat, 2),
                    "content": msg[:300], "prompt_tok": u.get("prompt_tokens"),
                    "completion_tok": u.get("completion_tokens"), "total_tok": u.get("total_tokens"),
                    "reasoning_tok": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except urllib.error.HTTPError as e:
        lat = time.time() - t0
        return {"seat": seat_no, "model": model, "http": e.code, "latency_s": round(lat, 2),
                "error": e.read().decode()[:200], "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as e:
        lat = time.time() - t0
        return {"seat": seat_no, "model": model, "http": -1, "latency_s": round(lat, 2),
                "error": str(e)[:200], "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

def main():
    model, s0, s1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    base, key = load_creds()
    out = os.path.join(OUTDIR, f"results_{model}.jsonl")
    done = set()
    if os.path.exists(out):
        for line in open(out):
            try: done.add(json.loads(line)["seat"])
            except Exception: pass
    next_allowed = 0.0
    for seat in range(s0, s1 + 1):
        if seat in done:
            continue
        rec = None
        for attempt, backoff in enumerate([0, 5, 15, 30]):
            wait = next_allowed - time.time()
            if wait > 0: time.sleep(wait)
            t_req = time.time()
            rec = call_model(base, key, model, seat)
            next_allowed = t_req + 1.15  # 1 QPS 阀
            if rec["http"] == 429 and attempt < 3:
                rec["retry_after_429"] = True
                with open(out, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                time.sleep(backoff)
                continue
            break
        with open(out, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"DONE {model} {s0}-{s1}")

if __name__ == "__main__":
    main()
