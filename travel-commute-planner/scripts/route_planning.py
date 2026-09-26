#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_planning.py — 高德 Web 服务路径规划（驾车/公交/步行/骑行 + 地理编码）
能力边界（已实测验证）：高德只给路线规划（距离/时间/驾车过路费），
**不提供铁路/航班票价**——票价用 train_query.py / flight_query.py。

前置：环境变量 AMAP_WEBSERVICE_KEY（高德开放平台「Web服务」类型 key，
     免费额度个人开发者 5000 次/日/接口）。未设置时打印申请指引并退出码 2。

用法：
  python3 route_planning.py geocode --address 中山大学广州校区南校园 --city 广州
  python3 route_planning.py drive --from "中山大学南校园" --to "顺德金榜牛奶街" --city 广州
  python3 route_planning.py transit --from "广州南站" --to "南沙院区" --city 广州
  python3 route_planning.py drive --from-loc 113.264,23.096 --to-loc 113.293,22.836
"""
import argparse, json, os, sys
import requests

KEY = os.environ.get("AMAP_WEBSERVICE_KEY", "").strip()
API = "https://restapi.amap.com"


def need_key():
    if KEY:
        return
    print("未检测到 AMAP_WEBSERVICE_KEY 环境变量。", file=sys.stderr)
    print("申请：高德开放平台 lbs.amap.com → 控制台 → 应用管理 → 创建应用 → 添加 Key（类型选 Web服务）", file=sys.stderr)
    print("设置：export AMAP_WEBSERVICE_KEY=你的key", file=sys.stderr)
    sys.exit(2)


def geocode(address, city=None):
    need_key()
    r = requests.get(f"{API}/v3/geocode/geo",
                     params={"key": KEY, "address": address, "city": city or ""}, timeout=15)
    d = r.json()
    if d.get("status") != "1" or not d.get("geocodes"):
        sys.exit(f"地理编码失败: {json.dumps(d, ensure_ascii=False)[:300]}")
    g = d["geocodes"][0]
    return {"location": g["location"], "formatted": g.get("formatted_address", address),
            "level": g.get("level", "")}


def direction(kind, origin, destination, city=None):
    need_key()
    eps = {"drive": "/v3/direction/driving", "transit": "/v3/direction/transit/integrated",
           "walk": "/v3/direction/walking", "bike": "/v4/direction/bicycling"}
    params = {"key": KEY, "origin": origin, "destination": destination}
    if kind == "transit":
        params["city"] = city or ""
        params["cityd"] = city or ""
    r = requests.get(API + eps[kind], params=params, timeout=20)
    return r.json()


def brief(d, kind):
    """提取核心结果"""
    try:
        if kind == "drive":
            p = d["route"]["paths"][0]
            return {"距离": f"{int(p['distance'])/1000:.1f}km",
                    "耗时": f"{int(p['duration'])//60}min",
                    "过路费": f"¥{p.get('tolls', '0')}",
                    "红绿灯": p.get("traffic_lights", "?")}
        if kind == "transit":
            t = d["route"]["transits"][0]
            return {"耗时": f"{int(t['duration'])//60}min",
                    "步行": f"{t.get('walking_distance', '?')}m",
                    "费用": f"¥{t.get('cost', '?')}",
                    "方案": " → ".join(
                        s.get("bus", {}).get("buslines", [{}])[0].get("name", s.get("type", ""))
                        for s in t.get("segments", []))[:200]}
        p = d["route"]["paths"][0] if "paths" in d.get("route", {}) else d["data"]["paths"][0]
        return {"距离": f"{int(p['distance'])/1000:.1f}km", "耗时": f"{int(p['duration'])//60}min"}
    except Exception:
        return {"raw": json.dumps(d, ensure_ascii=False)[:500]}


def main():
    ap = argparse.ArgumentParser(description="高德路径规划（需 AMAP_WEBSERVICE_KEY）")
    ap.add_argument("mode", choices=["geocode", "drive", "transit", "walk", "bike"])
    ap.add_argument("--address"); ap.add_argument("--city")
    ap.add_argument("--from", dest="frm"); ap.add_argument("--to", dest="to")
    ap.add_argument("--from-loc", help="lng,lat"); ap.add_argument("--to-loc", help="lng,lat")
    ap.add_argument("--json", action="store_true", help="输出原始JSON")
    a = ap.parse_args()

    if a.mode == "geocode":
        print(json.dumps(geocode(a.address, a.city), ensure_ascii=False, indent=1))
        return
    o = a.from_loc or geocode(a.frm, a.city)["location"]
    dst = a.to_loc or geocode(a.to, a.city)["location"]
    d = direction(a.mode, o, dst, a.city)
    if d.get("status") != "1":
        sys.exit(f"路径规划失败: {json.dumps(d, ensure_ascii=False)[:300]}")
    print(json.dumps(d if a.json else brief(d, a.mode), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
