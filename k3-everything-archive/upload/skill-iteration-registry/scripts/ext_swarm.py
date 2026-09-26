#!/usr/bin/env python3
"""外部蜂群编排器 v1.0（卡23/28 实装）
把 MaaS 纯端点模型编成应用层蜂群：工单模板 + 并发池 + 回执落盘 + usage 实测记账。
纪律：key 只读 <用户配置目录> 或 vault 持久层（卡29），禁打印/落盘；产出按 L1+unverified；
      单日金额闸 ¥5（卡28）；思考链限档（max_tokens 封顶）。
用法:
  python3 ext_swarm.py run <工单.json>     # 工单: {"mission": str, "workers":[{"seat","model","role","prompt_suffix"}]}
  python3 ext_swarm.py --balance           # 打印累计实测消耗
"""
import json, os, sys, hashlib, datetime, urllib.request
from concurrent.futures import ThreadPoolExecutor

CONF = os.path.expanduser("<用户配置目录>/external_seat.json")
VAULT = "<注册处>/vault/external_seat.json"  # 卡29回退
LEDGER = "<注册处>/蜂群消耗台账.jsonl"
RECEIPTS = "<输出区>/蜂群回执"
DAILY_CAP = 5.0  # 元
PRICE = {  # 时段2，元/百万token (in/out)
    "glm-5.2": (5.6, 19.6), "glm-5.1": (5.6, 19.6),
    "deepseek-v4-pro": (8.4, 16.8), "deepseek-v4-flash": (1.4, 2.8),
}

def load_conf():
    global CONF
    if not os.path.exists(CONF) and os.path.exists(VAULT): CONF = VAULT
    d = json.load(open(CONF))
    return d["base_url"].rstrip("/"), d["api_key"]

def chat(base, key, model, prompt, max_tokens=1500):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.2, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    u = d.get("usage", {})
    return d["choices"][0]["message"]["content"], u

def cost(model, u):
    pi, po = PRICE.get(model, (10.0, 20.0))
    return (u.get("prompt_tokens", 0) * pi + u.get("completion_tokens", 0) * po) / 1e6

def today_spend():
    today = datetime.date.today().isoformat()
    total = 0.0
    if os.path.exists(LEDGER):
        for line in open(LEDGER):
            try:
                e = json.loads(line)
                if e.get("date") == today: total += e.get("cost", 0)
            except Exception: pass
    return total

def run_worker(base, key, w, mission):
    prompt = f"【身份】你是外部蜂群的一名工蜂，席位={w['seat']}，角色={w['role']}。\n【任务】{mission}\n{w.get('prompt_suffix','')}\n【纪律】只输出实质内容；不得声称访问了你无法访问的资源；不确定就说不确定。"
    try:
        ans, u = chat(base, key, w["model"], prompt, w.get("max_tokens", 1500))
        c = cost(w["model"], u)
        return {"seat": w["seat"], "model": w["model"], "role": w["role"], "ok": True,
                "answer": ans, "usage": u, "cost": round(c, 4),
                "md5": hashlib.md5(ans.encode()).hexdigest()[:16]}
    except Exception as e:
        return {"seat": w["seat"], "model": w["model"], "role": w["role"],
                "ok": False, "error": str(e)[:300], "cost": 0.0}

def main():
    args = sys.argv[1:]
    if "--balance" in args:
        print(f"今日累计实测消耗: ¥{today_spend():.4f} / 闸 ¥{DAILY_CAP}")
        return
    if len(args) < 2 or args[0] != "run":
        print(__doc__); sys.exit(2)
    order = json.load(open(args[1]))
    if today_spend() >= DAILY_CAP:
        sys.exit("熔断：今日已达金额闸 ¥5，停件上报。")
    base, key = load_conf()
    os.makedirs(RECEIPTS, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results = list(ThreadPoolExecutor(max_workers=len(order["workers"])).map(
        lambda w: run_worker(base, key, w, order["mission"]), order["workers"]))
    batch_cost = sum(r["cost"] for r in results)
    for r in results:
        e = {"date": datetime.date.today().isoformat(), "ts": ts, "seat": r["seat"],
             "model": r["model"], "cost": r["cost"], "ok": r["ok"],
             "project": order.get("project", "未归属"), "skill": order.get("skill", "未归属"),
             "conv": order.get("conv", "未归属"),
             "usage": r.get("usage"), "md5": r.get("md5")}
        with open(LEDGER, "a") as f: f.write(json.dumps(e, ensure_ascii=False) + "\n")
    out = f"{RECEIPTS}/swarm_{ts}.md"
    with open(out, "w") as f:
        f.write(f"# 蜂群回执 {ts}\n\n任务: {order['mission'][:200]}\n本批成本: ¥{batch_cost:.4f}（今日累计 ¥{today_spend():.4f}）\n\n")
        for r in results:
            f.write(f"## 工蜂 {r['seat']}（{r['model']}·{r['role']}）\n")
            if r["ok"]:
                f.write(f"md5={r['md5']} cost=¥{r['cost']} usage={r['usage']}\n\n{r['answer']}\n\n")
            else:
                f.write(f"FAILED: {r['error']}\n\n")
    print(f"回执: {out}\n本批成本: ¥{batch_cost:.4f} | 今日累计: ¥{today_spend():.4f}")
    for r in results:
        print(f"  [{r['seat']}] {'OK' if r['ok'] else 'FAIL'} ¥{r['cost']}")

if __name__ == "__main__":
    main()
