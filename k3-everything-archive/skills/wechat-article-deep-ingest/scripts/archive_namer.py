#!/usr/bin/env python3
"""结构化命名 slug 生成。v1.0 2026-08-25 修改人: Orchestrator (Kimi K3)
用法: python3 archive_namer.py --topic 江苏十五五产业 --account singlewell --date 2026-01
"""
import argparse, re, sys

PINYIN_HINT = {"江苏":"jiangsu","浙江":"zhejiang","广东":"guangdong","四川":"sichuan","云南":"yunnan",
               "宁夏":"ningxia","江西":"jiangxi","陕西":"shaanxi","贵州":"guizhou","河南":"henan",
               "山东":"shandong","广西":"guangxi","北京":"beijing","上海":"shanghai","安徽":"anhui",
               "南京":"nanjing","产业":"industry","十五五":"15th5y","稀土":"rareearth","能源":"energy"}

def slugify(topic):
    t = topic.strip()
    for k, v in PINYIN_HINT.items(): t = t.replace(k, v+"-")
    t = re.sub(r"(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])", r"\1-", t)  # 仅独立数字段加分隔（v1.0.1修复回溯拆分bug）
    t = re.sub(r"[^A-Za-z0-9\-]+", "-", t).strip("-").lower()
    return re.sub(r"-{2,}", "-", t) or "untitled"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True); p.add_argument("--account", required=True)
    p.add_argument("--date", default="nd")
    a = p.parse_args()
    acct = re.sub(r"[^A-Za-z0-9]+", "", a.account).lower() or "unknown"
    print(f"{slugify(a.topic)}_{acct}_{a.date.replace('-','')}")

if __name__ == "__main__": main()
