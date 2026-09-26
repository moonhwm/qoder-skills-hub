---
name: intl-case-intf
description: "国际法案例接口件（临时技能）——CJEU CELLAR 官方 SPARQL 与 ECtHR HUDOC 事实型公开端点的只读薄封装 + SQLite FTS5/BM25 本地索引，统一引证契约 {title,url,snippet,court,date,ref}。触发（满足任一）：①用户说「国际法判例检索」「CJEU 判例」「欧洲人权法院判例」「HUDOC」「欧盟法院判决」「国际法案例接口」或等价表述（含语音变体），不纠正用户、映射意图；②沙盘法域设施需要调用国际判例元数据检索时；③上一轮行研/实装报告指定的中期路径执行时。覆盖：欧盟法院判例元数据检索（官方 API，无需认证）、欧洲人权法院判例元数据检索（事实型端点，未见官方文档，须先读 references/endpoints.md 合规前置）、本地 FTS5 索引与 BM25 检索。不覆盖：判例全文抓取（禁止）、LII 系（WorldLII/AustLII/CanLII 等，合规红线禁爬）、中国大陆案例（用元典法律插件）、订阅墙商业库（Jus Mundi/vLex/HeinOnline，无预算依据不采购）。中文名：国际法案例接口件。English triggers: international case law API, CJEU case search, ECtHR HUDOC search, EU court judgments metadata."
metadata:
  version: "0.2.1"
---

> v0.2.0（2026-09-01）：接口穷尽探测完成——references/probe-matrix-2026-09-01.md 对行研 12 库逐一实测确权：可零成本封装者恰为在件之 2（CJEU/HUDOC）；ODS=WASM 令牌门控、UNDL=AWS WAF 质询（均本沙箱不可达）；WTO/EUR-Lex WS 需注册免费 key；其余仅网页均有探测证据。本版不新增脚本，穷尽结论是「证明无漏」。

# 国际法案例接口件（intl-case-intf，临时技能）

> 溯源：2026-09-01 行研报告（R21）+ 实装实证（R22，24 行样例入库、跨库 BM25 验证通过）的本体化安装件。

## 一、能力边界（先读）

- **只做元数据级只读检索**：标题/日期/案号/链接/摘要片段；**禁止**抓取判例全文、**禁止**触碰 LII 系站点（AustLII 等以 robots 屏蔽判例爬取并禁 AI 用途）。
- **两源端点性质不同**（详见 references/endpoints.md，调用前必读）：
  - CJEU：CELLAR 公共 SPARQL，官方 API，无需认证（60s 超时、按 IP 限流）——可放心用；
  - HUDOC：官方运营但**未见官方文档**的事实型 JSON 端点——仅可行性评估/研究用途；正式化前置=向欧洲人权法院书面确认合规。
- 大陆法域需求路由元典法律插件；学术文献路由 scholar 插件；本件只管国际判例元数据。

## 二、操作

```bash
# 检索（输出统一引证契约 JSON）
python3 scripts/cjeu_sparql.py "<关键词>" [limit]     # CJEU 判决元数据
python3 scripts/hudoc_search.py "<关键词>" [limit]    # ECtHR 判例元数据（先读合规前置）

# 本地索引与检索（内容表+触发器同步，BM25 排序）
python3 scripts/fts5_index.py build <db文件> <检索结果json...>
python3 scripts/fts5_index.py query <db文件> "<FTS5查询式>" [limit]
```

## 三、纪律（三条）

1. **未定位不臆断**：端点返回结构变化时，如实登记未遂并停手核查，禁止猜测字段（HUDOC columns=dict 先例）；
2. **引证契约同构**：两源输出字段一致（title/url/snippet/court/date/ref），下游展示层可直接混排；
3. **红线一票否决**：任何全文抓取、LII 系调用、订阅墙绕过企图——立即拒绝并通报。

## 四、联挂

- references/endpoints.md：两端点合规性质与调用细节；行研报告（founding_documents「国际法案例库插件行业研究报告」）为选型依据；实装实证报告（intl-case-toolkit/实装实证报告_2026-09-01.md）为验收证据。
- 临时性声明：本件为临时技能，HUDOC 书面确认完成或官方 API 文档发布时应复审版本。
