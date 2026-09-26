# arXiv API 与 ID 体系契约

## 目录
- 第 1 节 arXiv ID 形制（新式/旧式/版本号）
- 第 2 节 官方元数据 API（export.arxiv.org）
- 第 3 节 search_query 检索语法速查
- 第 4 节 限速与礼貌使用纪律
- 第 5 节 失败处置：查不到 ≠ 不存在

## 第 1 节 arXiv ID 形制

| 形制 | 期间 | 形式 | 例子 |
|---|---|---|---|
| 新式 | 2007-04 至今 | `YYMM.NNNNN`（2015-01 起序号 5 位，此前 4 位） | `1706.03762`、`2405.12345` |
| 旧式 | 1991-08 ~ 2007-03 | `archive/YYMMNNN`（archive 可含连字符或大类.子类） | `hep-th/9901001`、`math.AG/0601001`、`cs/0607123` |

- **版本号**：`vN` 后缀（v1 起递增）。无后缀 = 未指定版本；网页端 `/abs/<id>` 默认跳最新版。
  引用纪律见 `citation_standards.md` 第 2 节——锁版本是防"版本漂移"的唯一手段。
- **提交年月即 ID 年月**：ID 的 YYMM 是首次提交（v1）年月，不因后续版本改变。一篇 2023 年大改的论文，
  其 ID 仍可能挂在 2017 年（如 1706.03762 到 v7 仍是 17 开头）——**不得用 ID 年月推断内容时效**。
- 校验/提取一律先用 `scripts/arxiv_id_check.py`（离线），它区分"格式错误"与"形制合法但可疑"
  （如未来年月、2015 后的 4 位序号——这两类是幻觉 ID 的高频形态）。

## 第 2 节 官方元数据 API

端点：`https://export.arxiv.org/api/query`（GET，返回 Atom XML）。

常用参数：

| 参数 | 说明 |
|---|---|
| `id_list` | 逗号分隔 ID（可带版本），批量核验用；单次建议 ≤50 个 |
| `search_query` | 检索式（第 3 节），与 id_list 二选一 |
| `start` / `max_results` | 分页；`max_results` 默认 10 |
| `sortBy` | `relevance` / `lastUpdatedDate` / `submittedDate` |

返回字段要点（`scripts/arxiv_fetch.py` 已解析为 JSONL）：

- `<id>`：含最新版本号的 abs URL——**API 永远按最新版返回**，要旧版须在网页或 `/abs/<id>vN` 核对；
- `<published>` = v1 提交时间，`<updated>` = 最新版时间（v1 论文两者相同）；
- `arxiv:journal_ref` / `arxiv:doi`：作者自填的发表信息——**有 ≠ 真的发表了**（作者可乱填），
  仅作"peer_review_hint"，确证发表须到期刊官网/Crossref 走 T2；
- `arxiv:comment` 含 "withdrawn" → 撤稿标记（脚本自动提取 `withdrawn: true`）。

网页核验入口（人工复核用）：`https://arxiv.org/abs/<id>`（摘要页，列全部版本与各版 diff 说明）。

## 第 3 节 search_query 检索语法速查

字段前缀：`ti:`（标题）`au:`（作者）`abs:`（摘要）`all:`（全字段）`cat:`（分类）。

- 组合：`AND` / `OR` / `ANDNOT`（**必须大写**），括号分组；
- 短语：`ti:"attention is all you need"`；
- 作者：`au:vaswani_a`（姓_名首字母更准）；
- 分类：`cat:cs.CL`；常用顶层类：`cs`、`math`、`physics`、`stat`、`eess`、`q-bio`、`econ`、`quant-ph`、`astro-ph`、`cond-mat`、`hep-*` 等。

例：`au:vaswani_a AND ti:attention`、`cat:cs.CL AND abs:"chain-of-thought"`。

## 第 4 节 限速与礼貌使用纪律

1. 连续 API 请求间隔 **≥3 秒**；`arxiv_fetch.py` 分批时自动 sleep(3)，不要在循环里并发轰炸。
2. 批量/全库元数据需求走官方镜像（Kaggle arXiv Dataset、S3 bulk access），**禁止**用本脚本爬全库。
3. 正文获取：PDF 用 `https://arxiv.org/pdf/<id>`；LaTeX 源码用 `https://arxiv.org/src/<id>`
   （部分论文不提供）。抓正文限速同 API。
4. 只做轻量核验时优先网页单篇页 + API 单批，不发起多余请求。

## 第 5 节 失败处置：查不到 ≠ 不存在

铁律（与 source-semantics-sentinel 的 Conflict→人工铁律同构）：

- **网络失败 / 超时 / 限流**：`arxiv_fetch.py` 退出码 2 + stderr 诊断。此时结论只能是"本次未核验"，
  禁止写成"论文不存在"。重试或人工到 arxiv.org 核对。
- **API 正常返回但某 ID 缺席**：脚本 stderr 打 `NOT_RETURNED` 清单。可能原因：ID 转写错误、
  幻觉 ID、论文被撤并。处置：先 `arxiv_id_check.py` 看形制可疑警告，再人工网页核对，
  仍查无 → 按"声称的论文不存在"登记 Conflict，交人工裁决，**不得静默丢弃该引用**。
- **标题/作者与声称不符**：形制合法、ID 存在，但元数据与引用方的声称对不上 = 典型"张冠李戴"，
  同样登记 Conflict，把两边原文摆出来交人工。
