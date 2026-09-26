#!/usr/bin/env python3
"""集群甲 · 双通道 POI 查询（高德主 + 百度备）
凭证隔离：从环境变量读取；缺失时自动 source <上传区>/credentials.env。
本脚本不含任何真实凭证，可随技能包外发；credentials.env 绝不可外发。

用法:
  python3 poi_query.py amap  "藤野造型" 西安        # 高德 POI 文本搜索（覆盖全）
  python3 poi_query.py amap-detail <poi_id>         # 高德详情（biz_ext 人均）
  python3 poi_query.py baidu "藤野造型" 西安        # 百度 POI 搜索（字段：人均+评分）
"""
import hashlib, json, os, subprocess, sys, urllib.parse, urllib.request

CRED = "<上传区>/credentials.env"
if not os.environ.get("AMAP_KEY") and os.path.exists(CRED):
    out = subprocess.run(["bash", "-c", f"source {CRED} && env"],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        k, _, v = line.partition("=")
        if k.startswith(("AMAP_", "BAIDU_")):
            os.environ[k] = v

def get(url):
    return json.load(urllib.request.urlopen(url, timeout=20))

def amap(path, params):
    params["key"] = os.environ["AMAP_KEY"]; params["output"] = "json"
    # 签名变体B（2026-08-26 实测仲裁）：参数名排序，value 原始值拼接（不编码）+ jscode → MD5
    raw = "&".join(f"{k}={v}" for k, v in sorted(params.items())) + os.environ["AMAP_JSCODE"]
    params["sig"] = hashlib.md5(raw.encode()).hexdigest()
    return get(f"https://restapi.amap.com{path}?{urllib.parse.urlencode(params)}")

def baidu(path, params):
    params["output"] = "json"; params["ak"] = os.environ["BAIDU_MAP_AK"]
    return get(f"https://api.map.baidu.com{path}?{urllib.parse.urlencode(params)}")

def main():
    ch = sys.argv[1]
    if ch == "amap":
        r = amap("/v3/place/text", {"keywords": sys.argv[2], "city": sys.argv[3],
                                    "citylimit": "true", "offset": "25", "page": "1"})
        print(f"status={r.get('status')} 命中={r.get('count')}")
        for p in r.get("pois") or []:
            print(f'- {p.get("name")} | {p.get("address")} | tel:{p.get("tel") or "—"} | id:{p.get("id")}')
    elif ch == "amap-detail":
        r = amap("/v3/place/detail", {"id": sys.argv[2]})
        print(json.dumps(r.get("pois"), ensure_ascii=False, indent=1))
    elif ch == "baidu":
        r = baidu("/place/v2/search", {"query": sys.argv[2], "region": sys.argv[3],
                                       "city_limit": "true", "scope": "2", "page_size": "20"})
        print(f"status={r.get('status')} 命中={r.get('total')}")
        for p in r.get("results") or []:
            di = p.get("detail_info") or {}
            print(f'- {p.get("name")} | {p.get("address")} | 人均:{di.get("price") or "—"} 评分:{di.get("overall_rating") or "—"}')

if __name__ == "__main__":
    main()
