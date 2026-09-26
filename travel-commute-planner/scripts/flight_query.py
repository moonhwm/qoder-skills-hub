#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flight_query.py — 航班比价链接生成器（方案A：零爬取、零风险）
原理：国内无免费官方航班查询 API（详见 references/data-sources.md）。
     本脚本不抓取任何 OTA 数据，只生成搜索结果页链接，用户/调用方打开即可看到实时票价。
     坚决不实现 JiPiao/MTOP 逆向爬虫——违反 OTA 服务条款，存在法律灰色地带。

用法：
  python3 flight_query.py --from 衡阳 --to 广州 --date 2026-09-01
  python3 flight_query.py --from SZX --to KMG --date 2026-09-25   # 支持 IATA 三字码
"""
import argparse, sys
from urllib.parse import quote

# 城市 → (携程/飞猪拼音码, IATA 主机场码)；无机场城市映射到就近枢纽
CITY = {
    "衡阳": ("hengyang", "HNY"), "广州": ("guangzhou", "CAN"), "深圳": ("shenzhen", "SZX"),
    "长沙": ("changsha", "CSX"), "东莞": ("shenzhen", "SZX"),  # 东莞无机场→深圳宝安
    "佛山": ("guangzhou", "CAN"), "北京": ("beijing", "BJS"), "上海": ("shanghai", "SHA"),
    "西安": ("xian", "SIA"), "成都": ("chengdu", "CTU"), "重庆": ("chongqing", "CKG"),
    "杭州": ("hangzhou", "HGH"), "昆明": ("kunming", "KMG"), "武汉": ("wuhan", "WUH"),
    "南京": ("nanjing", "NKG"), "厦门": ("xiamen", "XMN"), "海口": ("haikou", "HAK"),
    "三亚": ("sanya", "SYX"), "贵阳": ("guiyang", "KWE"), "南昌": ("nanchang", "KHN"),
    "合肥": ("hefei", "HFE"), "郑州": ("zhengzhou", "CGO"), "天津": ("tianjin", "TSN"),
    "青岛": ("qingdao", "TAO"), "大连": ("dalian", "DLC"), "沈阳": ("shenyang", "SHE"),
    "兰州": ("lanzhou", "LHW"), "乌鲁木齐": ("urumqi", "URC"), "珠海": ("zhuhai", "ZUH"),
    "澳门": ("macau", "MFM"), "香港": ("hongkong", "HKG"), "台北": ("taipei", "TPE"),
}
IATA2CITY = {v[1]: k for k, v in CITY.items()}


def resolve(name):
    name = name.strip()
    if name.upper() in IATA2CITY:
        name = IATA2CITY[name.upper()]
    if name not in CITY:
        return None
    return name, *CITY[name]


def links(frm_cn, dep_py, to_cn, arr_py, date):
    d_compact = date.replace("-", "")
    return {
        "去哪儿（支持中文直达）":
            f"https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport={quote(frm_cn)}"
            f"&searchArrivalAirport={quote(to_cn)}&searchDepartureTime={date}&nextNDays=0&startSearch=true",
        "携程":
            f"https://flights.ctrip.com/online/list/oneway-{dep_py}-{arr_py}?depdate={date}&cabin=y_s_c_f",
        "飞猪":
            f"https://sijipiao.fliggy.com/ie/flight_search_result.htm?tripType=0"
            f"&depCity={dep_py}&arrCity={arr_py}&depDate={d_compact}",
        "同程":
            f"https://flight.ly.com/?depart={quote(frm_cn)}&arrive={quote(to_cn)}&gopage=0&gotime={date}",
    }


def main():
    ap = argparse.ArgumentParser(description="航班比价链接生成器（零爬取）")
    ap.add_argument("--from", dest="frm", required=True)
    ap.add_argument("--to", dest="to", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    a = ap.parse_args()
    f, t = resolve(a.frm), resolve(a.to)
    if not f or not t:
        known = "、".join(sorted(CITY))
        sys.exit(f"未识别城市。已内置：{known}\n（其他城市请自行在 OTA 查询，或补充 CITY 表）")
    print(f"✈️  {f[0]}({f[2]}) → {t[0]}({t[2]})  {a.date}\n")
    for k, v in links(f[0], f[1], t[0], t[1], a.date).items():
        print(f"[{k}]\n  {v}\n")
    print("提示：以上为搜索页链接，打开即见实时票价；本工具不抓取、不缓存任何票价数据。")


if __name__ == "__main__":
    main()
