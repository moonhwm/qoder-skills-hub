#!/usr/bin/env python3
"""外部评审席自动调用器（v0.3.0 预置）
功能：把脱敏评审包发给外部模型（OpenAI 兼容接口，华为云 ModelArts MaaS 等），
收卷落盘，作为「外部第 6 席」意见入卷。
凭证：读 <用户配置目录>/external_seat.json（用户亲手放入）：
  {"base_url": "https://.../v1", "api_key": "...", "model": "模型名"}
纪律：禁打印/落盘 api_key；材料须为脱敏版（P0/P1 级）；调用记录入台账。
用法:
  python3 external_seat.py send <任务书.md> [--out <回执落盘.md>]
  python3 external_seat.py --check   # 只验凭证连通性
"""
import json, os, sys, hashlib, datetime, urllib.request, urllib.error

CONF = os.path.expanduser("<用户配置目录>/external_seat.json")
VAULT = "<注册处>/vault/external_seat.json"  # 卡29：持久层回退
def _resolve_conf():
    if os.path.exists(CONF): return CONF
    if os.path.exists(VAULT): return VAULT
    return CONF

def load_conf():
    CONF=_resolve_conf()
    if not os.path.exists(CONF):
        sys.exit(f"缺凭证文件 {CONF}（用户未放入）。格式见本脚本头部注释。")
    d = json.load(open(CONF))
    for k in ("base_url", "api_key", "model"):
        if not d.get(k): sys.exit(f"凭证缺字段: {k}")
    return d

def chat(conf, prompt):
    body = json.dumps({
        "model": conf["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        conf["base_url"].rstrip("/") + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + conf["api_key"]})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:500].decode(errors='replace')}")
    except Exception as e:
        sys.exit(f"调用失败: {e}")

def main():
    args = sys.argv[1:]
    conf = load_conf()
    if "--check" in args:
        ans = chat(conf, "回复两个字：正常")
        print("连通性 OK，模型回:", ans[:50]); return
    if not args or args[0] != "send" or len(args) < 2:
        print(__doc__); sys.exit(2)
    task = open(args[1], encoding="utf-8").read()
    ans = chat(conf, task)
    out = args[args.index("--out")+1] if "--out" in args else \
        f"<输出区>/外部席回执_{datetime.datetime.now():%Y%m%d_%H%M%S}.md"
    h = hashlib.md5(ans.encode()).hexdigest()[:16]
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# 外部第6席回执\n\n- 模型: {conf['model']}\n- 时间: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
                f"- md5[:16]: {h}\n- 任务书: {args[1]}\n\n## 回答原文\n\n{ans}\n")
    print(f"回执落盘: {out}\nmd5[:16]={h}\n前200字: {ans[:200]}")

if __name__ == "__main__":
    main()
