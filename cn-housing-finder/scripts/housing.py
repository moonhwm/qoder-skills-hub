#!/usr/bin/env python3
"""housing.py — 房源结构化解析器（cn-housing-finder 技能核心）

整合设计（2026-08-26 沙箱实测定稿）：
  搜索层  = web_search 工具（替代 cn-housing-mcp 的 DDG——沙箱境外不可达）
  抓取层  = web_open_url 工具（唯一过墙通道：直连 httpx 撞 antibot、obscura 空输出）
  解析层  = 本脚本：从 web_open_url 的 markdown 输出抽取结构化字段
           （原 cn-housing-mcp 的 JSON-LD 内核针对原始 HTML，本通道输出是 markdown，故重写文本解析器）

用法：
  python3 housing.py parse < page.md        # 单页 markdown → JSON
  python3 housing.py compare a.json b.json … # 多房源 → 对比表
"""
import json, re, sys

KNOWN_FACILITIES = ["床","衣柜","沙发","电视","冰箱","洗衣机","空调","热水器","宽带","暖气",
                    "燃气灶","阳台","卫生间","智能门锁","油烟机","可做饭"]

def parse_markdown(md: str, url: str = "") -> dict:
    out = {"url": url, "title": None, "price_month": None, "district": None, "biz_area": None,
           "rooms": None, "area_sqm": None, "facilities": [], "highlights": [],
           "building_type": None, "property_fee": None, "warnings": []}
    # 标题：首个 [^n^](url) 后同行文本
    m = re.search(r"\]\([^)]*\)\s*(.+)", md)
    if m: out["title"] = m.group(1).strip()[:80]
    # 价格：¥xx元/月 或 xx元/月 或 【xx元】
    m = re.search(r"(\d{3,6})\s*元\s*/?\s*月", md)
    if m: out["price_month"] = int(m.group(1))
    else:
        out["warnings"].append("price_not_found_in_text(可能在图片或未渲染区)")
    # 商圈：所属商圈：X / Y
    m = re.search(r"所属商圈[：:]\s*([^\s/]+)\s*/\s*([^\s\n]+)", md)
    if m: out["district"], out["biz_area"] = m.group(1).strip(), m.group(2).strip()
    # 户型与面积（"2室1厅"或"1室1卫"；"30平/43平米/54.79㎡"）
    m = re.search(r"(\d)室(\d)[厅卫]", md)
    if m: out["rooms"] = f"{m.group(1)}室{m.group(2)}{'厅' if '厅' in md[m.start():m.end()] else '卫'}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:㎡|平米|平方米|平)(?![米方])", md)
    if m: out["area_sqm"] = float(m.group(1))
    # 设施
    out["facilities"] = [f for f in KNOWN_FACILITIES if re.search(rf"^\s*-\s*{f}\s*$", md, re.M)]
    # 亮点：房屋亮点_a_ _b_（限定单行内，过滤空白残留）
    m = re.search(r"房屋亮点((?:_[^_]+)+?)\s*$", md, re.M)
    if m: out["highlights"] = [x.strip() for x in m.group(1).split("_") if x.strip()]
    m = re.search(r"建筑类型[：:]\s*(\S+)", md)
    if m: out["building_type"] = m.group(1)
    m = re.search(r"物业费用[：:]\s*([\d.]+)\s*元", md)
    if m: out["property_fee"] = float(m.group(1))
    # 风控信号
    if "验证" in md[:500] and not out["title"]: out["warnings"].append("possible_captcha")
    return out

def compare(files):
    rows = []
    for f in files:
        try: rows.append(json.load(open(f)))
        except Exception as e: print(f"skip {f}: {e}", file=sys.stderr)
    hdr = f"{'标题':<26} {'月租':>6} {'区域':<14} {'户型':<8} {'面积':>6}"
    print(hdr); print("-" * len(hdr.encode('gbk', 'ignore').decode('gbk', 'ignore')))
    for r in sorted(rows, key=lambda x: x.get("price_month") or 999999):
        print(f"{(r.get('title') or '?')[:24]:<26} {str(r.get('price_month') or '?'):>6} "
              f"{(r.get('district','') or '')+( '/' + r['biz_area'] if r.get('biz_area') else ''):<14} "
              f"{r.get('rooms') or '?':<8} {str(r.get('area_sqm') or '?'):>6}")
    if rows: print(f"\n共 {len(rows)} 套 | 月租区间 {min(r['price_month'] for r in rows if r.get('price_month'))}–{max(r['price_month'] for r in rows if r.get('price_month'))}" if any(r.get('price_month') for r in rows) else "")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "parse":
        md = sys.stdin.read()
        print(json.dumps(parse_markdown(md), ensure_ascii=False, indent=2))
    elif len(sys.argv) >= 3 and sys.argv[1] == "compare":
        compare(sys.argv[2:])
    else:
        print(__doc__)
