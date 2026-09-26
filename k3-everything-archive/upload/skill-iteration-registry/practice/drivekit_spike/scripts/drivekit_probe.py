#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drivekit_probe.py — 华为云空间 Drive Kit 无凭证存活探针（spike 实践件 v1.0 / 2026-08-31）

用途：探测 Drive Kit REST 与 OAuth 端点是否存活、错误码形态。
纪律：不携带任何凭证；401/400 即预期应答（证明服务存活且闸门在轨）。
      本脚本不执行任何授权、不上传下载任何用户文件。

实测基线（2026-08-31）：
  P1 files 端点   -> HTTP 401  errorCode 21000401 "authorization header not exist."
  P2 about 端点   -> HTTP 401  同上
  P3 token 端点   -> HTTP 400  error 1102 "missing required parameter: client_id"
  P4 authorize页  -> HTTP 200  返回 OAuth 登录/错误页 HTML
"""
import json, sys, time, urllib.request, urllib.error

UA = {"User-Agent": "drivekit-spike-probe/1.0 (no-credential liveness check)"}

PROBES = [
    ("P1_files",     "GET",  "https://driveapis.cloud.huawei.com.cn/drive/v1/files", None, 401),
    ("P2_about",     "GET",  "https://driveapis.cloud.huawei.com.cn/drive/v1/about", None, 401),
    ("P3_token",     "POST", "https://oauth-login.cloud.huawei.com/oauth2/v3/token", b"", 400),
    ("P4_authorize", "GET",  "https://oauth-login.cloud.huawei.com/oauth2/v3/authorize?response_type=code", None, 200),
]

def run():
    report = {"probe_ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "results": []}
    for name, method, url, data, expect in PROBES:
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                code, body = r.status, r.read(600)
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read(600)
        except Exception as e:
            code, body = -1, str(e).encode()
        ms = round((time.time() - t0) * 1000)
        ok = (code == expect)
        report["results"].append({
            "probe": name, "url": url, "method": method,
            "http": code, "expect": expect, "verdict": "ALIVE_GATED" if ok else "UNEXPECTED",
            "ms": ms, "body_head": body.decode("utf-8", "replace")[:300],
        })
        print(f"[{name}] HTTP {code} (expect {expect}) {'OK' if ok else '!!'} {ms}ms")
        time.sleep(1)
    report["summary"] = "all-alive-gated" if all(r["verdict"] == "ALIVE_GATED" for r in report["results"]) else "anomaly"
    return report

if __name__ == "__main__":
    rep = run()
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1)
        print("saved:", out)
    sys.exit(0 if rep["summary"] == "all-alive-gated" else 1)
