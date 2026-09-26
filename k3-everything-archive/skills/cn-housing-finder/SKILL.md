---
name: cn-housing-finder
description: 国内租房/买房房源初筛与结构化——web_search 初筛 + web_open_url 抓详情 + 本地解析器出对比表。当用户要"找房/租房/买房/房源对比/看房清单"时触发。整合自 zhangchushu/cn-housing-mcp（解析内核思路），但抓取层按沙箱实测重构（2026-08-26）。
---

# cn-housing-finder · 房源初筛结构化

## 三式工作流（实测验证的唯一可行链路）

```
1. web_search 初筛：「{城市} 租房 整租 {商圈/地铁/预算}」→ 收集候选 URL（58/安居客/房天下）
2. web_open_url 逐个抓详情 → 输出存 /tmp/house_N.md
3. python3 scripts/housing.py parse < /tmp/house_N.md > /tmp/house_N.json   # 结构化
   python3 scripts/housing.py compare /tmp/house_*.json                      # 对比表（按月租排序）
```

## 抓取层实测记录（valid_asof=2026-08-26；复测触发：obscura升级/58换风控/web_open_url失效）

| 通道 | 结果 |
|---|---|
| 直连 httpx（原 cn-housing-mcp 方式） | ❌ 302 → callback.58.com/antibot 验证码墙（58/安居客实锤） |
| obscura --stealth | ❌ 空输出 |
| **web_open_url** | ✅ **唯一过墙通道**（全文 markdown：标题/设施/亮点/商圈/物业费） |
| 原 DDG 搜索层 | ❌ 境外站沙箱不可达 → 由 web_search 替代 |

## 解析器字段与局限

- 抽取：title / price_month / district / biz_area / rooms / area_sqm / facilities(16项白名单) / highlights / building_type / property_fee
- **价格常缺失**：58 详情页价格常在图片区，文本抽不到时 warnings 标注（正常，以 App 实价为准）
- 房天下列表页 301 后 200 但无结构化字段——只作 URL 来源，不作解析对象
- 低频使用（每次 ≤5 页），撞 captcha 即停（不绕风控红线）

## 合规红线（沿用原项目姿态）

不绕验证码、不高频并发、不在数据中心 IP 上跑批量抓取；遇拦截改"贴链接 → 分析"模式。
