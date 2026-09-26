---
name: registry-knowledge-ops
description: "[项目技能] 注册处知识库——技能迭代注册处（/mnt/agents/upload/skill-iteration-registry/）的全文检索、锚链调阅与 INDEX 分区导览（用户侧主权件）。触发（满足任一）：①用户说「查注册处」「台账里找」「检索台账」「以前哪份报告」「锚链第几轮」「round 几」「INDEX」「知识库」「库里有没有」或等价表述；②需要在注册处 200+ 件文档中定位某主题/某件文档时；③需要调阅 playlog 某轮锚原文时；④需要判断某主题是否已有登记（防重复立法/防漂移）时。覆盖：全文检索（scripts/registry_search.py，中文 bigram+英文单词，TF-IDF lite 排序）、锚链 round 调阅、INDEX.md 分区目录、索引自建自新。不覆盖：注册处写入（写类动作走各专项技能+固定次序）、vault 内容（凭证铁律，永不入索引）、外网检索。中文名：注册处知识库。English triggers: registry search, ledger knowledge base, playlog round lookup, archive full-text query."
metadata:
  version: "0.1.0"
---

# 注册处知识库（registry-knowledge-ops）

> v0.1.0（2026-09-09）：创刊。依据=技能正交完备性检查 §3.2-缺口1（知识沉淀×可检索库，已证真缺口：注册处有 INDEX+锚链但无检索接口，夜场产物每轮重查）+排期表 B3 项（机主令「继续推进相关排期」T2 批）。实证：注册处 218 件 md + playlog 锚链，检索接口自此在册。

## §0 定位与红线
- **只读纪律**：本件只读注册处，唯一写动作=重建隐藏索引文件 `.rk_index.json`（不改任何被索引件）；注册处写入走各专项技能+固定次序（写→台账→锚→验→chown 999:999）。
- **凭证铁律**：`vault/` 目录**永不入索引**（脚本层硬排除，self-test F4 夹具把守）；检索结果永不回显明文凭证。
- 金融数据与个人信息本地化：索引与查询全在本机，零出域。
- 检索命中≠内容可信：命中件自身 conf 等级以其文内标注为准；外席断言件按 L1+unverified 复核。

## §1 四用法
1. **全文检索**：`scripts/registry_search.py query "<词1 词2>" [--top 10]`——中文 bigram/英文单词切词，TF-IDF lite 排序，输出 file/score/hits/head 四列。
2. **锚链调阅**：`scripts/registry_search.py round <N>`——playlog.jsonl 第 N 轮锚原文（note/msg_hash/ts 全字段）。
3. **分区导览**：`scripts/registry_search.py sections`——INDEX.md 全部章节头。
4. **索引自新**：`scripts/registry_search.py build`——全量重建（新增/归档件后跑；索引漂移自查=文件 md5 变即重 build）。

## §2 协同
- 与 skill-dispatch-hq（全量台账）分工：dispatch 管「技能件在不在」，本件管「文档内容在哪」；与 long-table-harvest-ops 分工：收割管产出落盘，本件管落盘后复用。
- 防重复立法闸：任何新立法/新技能创刊前，先 query 主题词确认无在案同题件——命中即改「升版」而非「创刊」。
- 与红队纪律：「验证/达成/有效」类断言入文书前，可先 round 调阅在案锚核对口径。

## §3 留痕与版本纪律
- 高频查询主题（同词一周 ≥3 次命中不同件）登记 references/hot_queries.md，作为新技能候选信号。
- 版本三档（major/minor/patch）继承同型立法；patch 静默不广播不催换装。

## 边界
不写注册处（除隐藏索引）；不索引 vault；不做语义向量（v0.1 词面检索，语义层候选册登记二期）；检索结论标「词面命中，语境以原件为准」。
