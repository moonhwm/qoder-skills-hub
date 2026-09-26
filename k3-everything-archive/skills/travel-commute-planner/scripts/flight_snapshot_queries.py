#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flight_snapshot_queries.py — 机票「搜索快照实测」查询串生成器（纯标准库）

OTA 列表页在自动化环境常被反爬/超时（实测：携程/去哪儿/同程/Trip.com 直连均失败）。
本脚本为 Layer 1.5「搜索快照实测」生成即用的搜索引擎查询串；agent 用 web_search 执行后，
从快照中提取带日期的真实报价（携程 m 站航线页 / 天巡 Skyscanner / 媒体行情稿），
按 references/module-flight.md 的 Layer 1.5 规程登记为 conf=C级（快照实测）。

用法：
  python3 flight_snapshot_queries.py --from 长沙 --to 成都 --date 2026-09-10
  python3 flight_snapshot_queries.py --batch routes.json   # [{"from":"长沙","to":"成都","date":"2026-09-10"},...]
输出：每航线 4 条查询串（OTA m 站 / 天巡 / 媒体行情 / 通用），可直接喂 web_search。
"""
import argparse, json, sys

TEMPLATES = [
    ("ota_m",    "{f}飞{t} {d} 机票 携程"),                    # 命中携程m站航线页快照（dated低价日历）
    ("skyscanner", "{f}到{t} 机票 天巡 Skyscanner"),            # 命中天巡航线页（往返/单程/最低价月份）
    ("media",    "{f}飞{t} 机票 价格 {y}年{m}月"),             # 命中媒体行情稿（新浪/澎湃出行版）
    ("generic",  "{f}到{t} 特价机票 最低价格"),                 # 兜底
]

def queries(frm, to, date):
    y, m = date[:4], str(int(date[5:7]))
    return [{"lane": f"{frm}→{to}", "channel": k, "query": t.format(f=frm, t=to, d=date, y=y, m=m)} for k, t in TEMPLATES]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm"); ap.add_argument("--to"); ap.add_argument("--date")
    ap.add_argument("--batch", help='routes.json: [{"from","to","date"},...]')
    a = ap.parse_args()
    routes = json.load(open(a.batch, encoding="utf-8")) if a.batch else [{"from": a.frm, "to": a.to, "date": a.date}]
    out = []
    for r in routes:
        if not (r.get("from") and r.get("to") and r.get("date")):
            print(f"[skip] 缺 from/to/date: {r}", file=sys.stderr); continue
        out += queries(r["from"], r["to"], r["date"])
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
