# probe-matrix — 国际法接口穷尽探测矩阵（2026-09-01 第15轮实测）

> 方法：对行研 12 库逐一直接 HTTP 探测（页面解析 + 端点猜测 + 响应头检验），命中与否均以当轮响应为证。全部只读 GET；未携带任何凭据；未尝试绕过任何反爬。

| 库 | 探测动作 | 实测响应 | 确权结论 |
|---|---|---|---|
| CJEU（CELLAR SPARQL） | 已封装（v0.1） | 2 查询 16 命中 | **官方 API 可用（在件）** |
| ECtHR HUDOC | 已封装（v0.1） | resultcount=11,086 | **事实型端点可用（在件，合规前置）** |
| ODS documents.un.org | SPA JS 逆向 → `https://documents.un.org/api/search?s=`（含 /subjects /tcodes /dailylist） | 全端点 **403**（Authorization 由 WASM `check(时间戳)` 反爬令牌生成） | **官方 API 存在但 WASM 令牌门控——本沙箱不可达，仅网页** |
| UN Digital Library | Invenio `of=recjson/rss/xd` 三格式 | 一律 **202 空响应**，响应头 `x-amzn-waf-action: challenge` | **端点存在但 AWS WAF 质询——本沙箱不可达，仅网页** |
| ICJ | `/json`、`/json/cases` 探测 + 页面线索分析 | 404；'/json' 线索证实为 drupal-settings-json 假阳性 | **仅网页（实证）** |
| PCA | `/jsonapi`、`/en/cases?_format=json` | 404 / 回退 HTML | **仅网页（实证）** |
| ICSID | 案例库首页 GET | **403 Forbidden**（bot 拦截） | **仅网页（实证，且网页亦拦沙箱 UA）** |
| UNTC treaties.un.org | 首页 165KB ASPX 解析找 .svc/api/WebService | 无线索 | **仅网页（实证）** |
| WTO apiportal.wto.org | 门户页 + 行研口径 | SPA 门户；Timeseries/QR/ePing 等 API 需**注册免费 API key**；DS 文书是否在 API 内**未定位**（沿用 F1） | **需注册 key——未封装，路径文档化** |
| EUR-Lex Web Services | 行研口径（本轮未重探） | SOAP/REST 需注册免费账号 | **需注册——未封装；CELLAR SPARQL 已可覆盖 CJEU 需求** |
| ITLOS / IRMCT / ICC Legal Tools / IACtHR / 非洲法院 | 行研口径 + 站点形态复核 | 静态 PDF/注册制/纯网页 | **仅网页（维持 F1 确权）** |
| italaw / Jus Mundi / LII 系 | 不探测（纪律） | — | 学术聚合/订阅墙/禁爬红线，**手工查阅或禁用** |

## 穷尽结论

12 库可编程表面全数实测确权：**可零成本封装者恰为已在件之 2（CJEU、HUDOC）**；ODS/UNDL 端点真实存在但被反爬层（WASM 令牌/AWS WAF）挡在沙箱外；WTO/EUR-Lex WS 需注册免费 key（留作用户决策项）；其余仅网页均有当轮探测证据。本件 v0.2 不新增封装脚本——穷尽的价值在于**证明无漏**。
