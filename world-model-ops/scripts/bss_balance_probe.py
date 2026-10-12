# -*- coding: utf-8 -*-
"""bss_balance_probe.py —— 以令条指定之 AK/SK 查阿里云账务余额（判 A1 之性质）
★用途：若余额充足而百炼仍报 403/429，则"仅用免费额度"之设置即唯一障碍（A1 判据）。
★纪律：密钥仅内存读取、不打印、不落盘；仅输出状态码与金额。
（中文串一律用「」）
"""
import base64, csv, hashlib, hmac, json, pathlib, sys, time, urllib.parse, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8")
D = pathlib.Path.home()/"OneDrive"/"桌面"
def read_key(fn):
    t = (D/fn).read_bytes().decode("utf-8-sig", "replace")
    rows = [r for r in csv.reader(t.splitlines()) if any((c or "").strip() for c in r)]
    # ★表头行须跳过：取"看起来不像列名"的第一行
    for r in rows:
        a = (r[0] or "").strip(); b = (r[1] or "").strip() if len(r) > 1 else ""
        if a and b and "AccessKey" not in a and "Secret" not in a and len(a) >= 12 and len(b) >= 12:
            return a, b
    raise SystemExit("★未在 CSV 中找到数据行（仅表头？）")
def rpc(ak, sk, endpoint, version, action, extra=None):
    p = {"AccessKeyId": ak, "Action": action, "Format": "JSON", "SignatureMethod": "HMAC-SHA1",
         "SignatureNonce": str(int(time.time()*1000)) + str(int(time.perf_counter()*1000) % 1000),
         "SignatureVersion": "1.0", "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "Version": version}
    if extra: p.update(extra)
    q = "&".join("%s=%s" % (urllib.parse.quote(k, safe=""), urllib.parse.quote(str(v), safe="")) for k, v in sorted(p.items()))
    sts = "GET&%2F&" + urllib.parse.quote(q, safe="")
    sig = base64.b64encode(hmac.new((sk + "&").encode(), sts.encode(), hashlib.sha1).digest()).decode()
    url = "https://%s/?Signature=%s&%s" % (endpoint, urllib.parse.quote(sig, safe=""), q)
    r = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(r, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return -1, str(e)[:150]
for fn, label in (("AccessKey 阿里云百炼主账户.csv", "主账户(root)"), ("AccessKey RAM角色.csv", "RAM角色(power-application-user)")):
    ak, sk = read_key(fn)
    print("  ═══ %s（AK %s…，len=%d）═══" % (label, ak[:6], len(ak)))
    st, j = rpc(ak, sk, "business.aliyuncs.com", "2017-12-14", "QueryAccountBalance")
    if isinstance(j, dict):
        d = j.get("Data") or {}
        print("   QueryAccountBalance ⇒ HTTP %s ｜ Code=%s ｜ 可用余额=%s %s ｜ 币种=%s ｜ 信控额度=%s" % (
            st, j.get("Code"), d.get("AvailableAmount"), d.get("Currency"), d.get("Currency"), d.get("CreditAmount")))
        if j.get("Message"): print("      Message=%s" % str(j["Message"])[:120])
    else:
        print("   ⇒ HTTP %s ｜ %s" % (st, str(j)[:200]))
    st2, j2 = rpc(ak, sk, "business.aliyuncs.com", "2017-12-14", "QueryAccountBalance", {"Bid": ""})
    if isinstance(j2, dict) and j2.get("Code") and j2.get("Code") != "Success":
        print("   （复核同）Code=%s Message=%s" % (j2.get("Code"), str(j2.get("Message"))[:100]))
