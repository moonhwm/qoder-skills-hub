#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_query.py — 12306 官方接口火车票精确查询（余票/时刻/票价，免 key）
数据源：12306 leftTicket/queryG + queryTicketPrice（公开接口，数据来自官方）

用法：
  python3 train_query.py --from 衡阳东 --to 广州南 --date 2026-08-26
  python3 train_query.py --batch pairs.json --date 2026-08-26 --out fares.csv
  python3 train_query.py --stations 衡阳          # 模糊查车站码

pairs.json: [{"from":"衡阳东","to":"广州南"}, ...]
注意：12306 有反爬——必须先访问 init 页取 Cookie（本脚本自动），请求间隔 ≥0.2s；
     同区间同车型票价一致，默认抽样（3G+2D/C+2普速），--full 逐车查（慢）。
"""
import argparse, json, sys, time
import requests

BASE = "https://kyfw.12306.cn/otn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
}
SEAT_MAP = {"A9": "商务座", "P": "特等座", "M": "一等座", "O": "二等座",
            "A1": "硬座", "A2": "软座", "A3": "硬卧", "A4": "软卧",
            "A6": "高级软卧", "F": "动卧", "WZ": "无座", "B1": "无座",
            "AI": "二等卧(动集)", "AJ": "一等卧(动集)"}
# 余票字段索引（queryG result 按 | 分隔）
LEFT_SEAT = {21: "高级软卧", 23: "软卧/一等卧", 24: "软座", 26: "无座",
             28: "硬卧/二等卧", 29: "硬座", 30: "二等座", 31: "一等座",
             32: "商务座/特等座", 33: "动卧"}


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(f"{BASE}/leftTicket/init", params={"linktypeid": "dc"}, timeout=20)
    return s


def load_station_map(sess):
    js = sess.get(f"{BASE}/resources/js/framework/station_name.js", timeout=20).text
    m = {}
    for part in js.split('@')[1:]:
        f = part.split('|')
        if len(f) >= 3:
            m[f[1]] = f[2]
    return m


def parse_train(item):
    f = item.split('|')
    seats = {LEFT_SEAT[i]: f[i] for i in LEFT_SEAT
             if i < len(f) and f[i] not in ("", "--", "无")}
    return {"train_no": f[2], "code": f[3], "dep": f[8], "arr": f[9],
            "dur": f[10], "from_no": f[16], "to_no": f[17],
            "seat_types": f[35], "left": seats}


def query_tickets(sess, date, fc, tc):
    r = sess.get(f"{BASE}/leftTicket/queryG",
                 params={"leftTicketDTO.train_date": date,
                         "leftTicketDTO.from_station": fc,
                         "leftTicketDTO.to_station": tc,
                         "purpose_codes": "ADULT"}, timeout=25)
    return r.json().get("data", {}).get("result", [])


def query_price(sess, t, date):
    try:
        r = sess.get(f"{BASE}/leftTicket/queryTicketPrice",
                     params={"train_no": t["train_no"], "from_station_no": t["from_no"],
                             "to_station_no": t["to_no"], "seat_types": t["seat_types"],
                             "train_date": date}, timeout=20)
        d = r.json().get("data", {})
        return {SEAT_MAP.get(k, k): v for k, v in d.items()
                if isinstance(v, str) and v.startswith("¥")}
    except Exception:
        return {}


def sample(result, n_g=3, n_d=2, n_k=2):
    gs = [x for x in result if x.split('|')[3].startswith('G')]
    ds = [x for x in result if x.split('|')[3][0] in 'DC']
    ks = [x for x in result if x.split('|')[3][0] in 'KTZ' or x.split('|')[3][0].isdigit()]
    return (gs[:n_g] + ds[:n_d] + ks[:n_k]) or result[:4]


def main():
    ap = argparse.ArgumentParser(description="12306 火车票精确查询（免key）")
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    ap.add_argument("--date", help="乘车日期 YYYY-MM-DD（须在预售期内）")
    ap.add_argument("--batch", help="pairs.json 批量模式")
    ap.add_argument("--full", action="store_true", help="逐车查价（慢）")
    ap.add_argument("--stations", help="模糊查询车站码后退出")
    ap.add_argument("--out", help="输出 CSV 路径")
    a = ap.parse_args()

    sess = make_session()
    smap = load_station_map(sess)
    if a.stations:
        hits = {k: v for k, v in smap.items() if a.stations in k}
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return
    if not a.date:
        ap.error("需要 --date")
    pairs = json.load(open(a.batch, encoding="utf-8")) if a.batch else (
        [{"from": a.frm, "to": a.to}] if a.frm and a.to else ap.error("需要 --from/--to 或 --batch"))

    rows = []
    for p in pairs:
        fc, tc = smap.get(p["from"]), smap.get(p["to"])
        if not fc or not tc:
            print(f"[skip] 未找到车站: {p}", file=sys.stderr)
            continue
        result = query_tickets(sess, a.date, fc, tc)
        for item in (result if a.full else sample(result)):
            t = parse_train(item)
            row = {"区间": f"{p['from']}→{p['to']}", "车次": t["code"],
                   "出发": t["dep"], "到达": t["arr"], "历时": t["dur"],
                   "当日车次总数": len(result)}
            row.update({f"票价_{k}": v for k, v in query_price(sess, t, a.date).items()})
            row.update({f"余票_{k}": v for k, v in t["left"].items()})
            rows.append(row)
            time.sleep(0.2)
        print(f"[ok] {p['from']}→{p['to']}: 当日{len(result)}趟", file=sys.stderr)

    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        print(df.to_string(index=False))
        if a.out:
            df.to_csv(a.out, index=False, encoding="utf-8-sig")
            print(f"\n已保存: {a.out}", file=sys.stderr)
    except ImportError:
        print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
