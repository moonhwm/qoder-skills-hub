# access-routes.md — 需注册接口的申请途径（2026-09-01 检索核实）

> 本件 v0.2 穷尽探测确认的「需注册」与「可申请」通道，逐条给申请路径。访问日期 2026-09-01。

## 1. WTO API Developer Portal（免费 key，自助）

- **入口**：https://apiportal.wto.org/signup （官网自述「Just sign up for an API key and start consuming APIs right away. It is free.」）
- **步骤**：① Sign up 注册账号 → ② 登录后于 **Products** 页订阅 **Standard** 产品（WTO Stats User Guide 口径：注册并订阅 Standard 后发放 subscription key）→ ③ 在账户 **profile 页**取 key。
- **可得 API**：Timeseries（货物/服务贸易统计、关税）、Quantitative Restrictions、ePing（通报预警）等；**争端解决（DS）文书是否在 API 内仍未定位**（F1 口径维持；第三方 api-evangelist 索引称含 dispute settlement records，未见 WTO 官方文档确认）。
- **key 调用形态**：Ocp-Apim-Subscription-Key 头（APIM 标准）。

## 2. EUR-Lex Web Service（SOAP，免费，人工审批）

- **入口**：https://eur-lex.europa.eu/content/help/data-reuse/webservice.html 的 **Webservice registration** 链接。
- **步骤**（官方帮助页六步）：① 点 Webservice registration → ② 无 EU Login 账号先 **Register** 注册欧盟统一登录 → ③ **Sign in** → ④ 点 **Register** 填申请表 → ⑤ **Save** 提交 → ⑥ **管理员人工审核**，通过后**邮件发送访问权限**（用户名/密码 + WSDL 链接 `https://eur-lex.europa.eu/EURLexWebService?WSDL`）。
- **能力边界**（官方手册）：专家检索式查询 EUR-Lex 全部元数据，**不能直接取全文**（全文走 CELLAR REST/URI server——后者无需注册，本件已封装 SPARQL 通道）；**2026-01-01 起单次检索结果上限 10,000 条**；大批量需求官方指引走 CELLAR API / Data Dump。
- **审批性质**：管理员 check 后可批准或拒绝（官方手册原文），非即时自助。

## 3. CanLII API（免费 key，人工审核，研究/教育用途优先）

- **入口**：CanLII 官方 API 文档（github.com/canlii/API_documentation）——「To apply for an API key, please send a message with your contact information to the feedback form」；反馈表：https://www.canlii.org/en/feedback/feedback.html （另一官方入口为 canlii.org/en/api 页面）。
- **申请要点**：说明项目范围（describe the scope of your project）；**研究/教育用途一般顺利获批**，但为**人工审核**，需提前申请。
- **条款边界**：**仅元数据**（题名/引证/日期/关键词/引证关系），**不提供判决全文**（全文回链 canlii.org 页面）；禁止再托管/再分发底层文献。
- **速率**：1 并发、2 次/秒、**5,000 次/日硬顶**（CanLII 官方条款）。

## 4. 对照与弃用登记

| 通道 | 结论 | 一句理由 |
|---|---|---|
| CourtListener（美国） | 参考样板，不申请 | OAuth 2.0 免费自助（官方 MCP 同钥），但法域为美国判例，超出国际法选型范围 |
| AustLII Virtual Data Lab | 弃用 | 收费、数据不出环境的折中方案，与沙盘零采购口径不符；且其判例禁爬红线不变 |
| Jus Mundi / vLex / HeinOnline / OPIL | 弃用 | 订阅墙报价制，无预算依据 |

## 5. 建议申请次序（若获所有者批准）

1. **WTO**（纯自助、即时）——若 DS 文书在 API 内则收益最大，不在则贸易统计对宏观研究亦有用；
2. **CanLII**（人工审核周期未知，宜早递）——英联邦判例元数据补盲；
3. **EUR-Lex WS**——CELLAR SPARQL 在件已覆盖 CJEU 判例核心需求，WS 仅在需要专家检索式全文元数据检索时值得申请。
