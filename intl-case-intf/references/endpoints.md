# endpoints.md — 两端点合规性质与调用细节（2026-09-01 实测）

## 1. CJEU — CELLAR 公共 SPARQL（官方 API）

- 端点：`https://publications.europa.eu/webapi/rdf/sparql?query=...&format=application/sparql-results+json`
- 性质：**官方 API，无需认证**；限制：60 秒查询超时、按 IP 限流（EUR-Lex/CELLAR 官方文档口径）。
- 数据范围：1952 年至今欧洲法院/普通法院判决元数据（CELEX 6* 类，24 种欧盟语言；本件取 ENG 表达式标题）。
- 结果 url 为 CELLAR resource URI；eurlex 字段拼 `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}` 供人工打开。
- 已知瑕疵：title 含 `#` 分隔的多段元数据（审判庭/当事人/案由/案号），v0.2 列清洗事项。
- 批量下载替代：EU Open Data Portal 提供周更 RDF 全量包（本件未封装，需要时再扩）。

## 2. ECtHR — HUDOC 事实型公开 JSON 端点（未见官方文档）

- 端点：`https://hudoc.echr.coe.int/app/query/results?query=...&select=...&start=0&length=N`
- 性质：欧洲人权法院**官方运营**、学术/开源项目长期作为 API 使用、无需认证；但**未见正式 API 文档**（官方仅发布 HUDOC 使用手册 PDF，述 UI 而非 API）。
- **合规前置（强制）**：正式化/规模化使用前，应向欧洲人权法院书面确认；当前仅限可行性评估与研究用途的低频只读调用。
- 查询语法：`contentsitename:ECHR AND (<关键词>)`；select 常用字段：itemid,docname,appno,conclusion,judgementdate,importance,respondent,doctype。
- 返回结构实测（2026-09-01）：`results[].columns` 为 **dict**（非 list）；`judgementdate` 形为 `DD/MM/YYYY HH:MM:SS`（本件转 ISO）；press release 类条目可能无 judgementdate（留空不臆造）。
- 正文另有 `…/app/conversion/docx/html/body` 端点可取正文——**本件不封装**（元数据级边界）。

## 3. 红线清单（复述）

- LII 系（WorldLII/AustLII/CanLII/BAILII/NZLII/HKLII/SAFLII 等）：robots 屏蔽判例爬取 + 禁 AI 用途——**一律不调**；
- Jus Mundi/vLex/HeinOnline/OPIL 等订阅墙：无预算依据，不采购、不绕过；
- 中国大陆案例：路由元典法律插件（agent-gw，在册实测在线）。
