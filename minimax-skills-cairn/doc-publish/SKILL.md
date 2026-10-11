---
name: doc-publish
description: 出件（七步 SOP：打钟/闸/签/投）（MiniMax 设计/编码技能包 v1.2.0；由 A2A新席_石敢当Cairn 贡献）
---

# 出件（七步 SOP：打钟/闸/签/投）

## 何时用
须产出正式件并投递入账时

## 系统提示
你是本席之出件员。按七步执行并回报每步结果；禁止手写时点；禁止在件中留凭据。中文。

## 步骤
1. 写正文（含档号/席位/性质/请求/声明）
2. 打钟
3. 术语闸
4. v5 署签
5. 抄送四处（交换区/总线目录/docx/镜像落点）
6. 总线 emit
7. 双仓 commit+push（push_all.py）

## 命令
- `python exp/stamp_time.py <件>`
- `python exp/termtable.py check --paths <件>`
- `python exp/sig_block.py --file <件> --append --note "<注>"`
- `python exp/lsbus_format_ops.py emit --bus <bus.jsonl> --path <件> --kind artifact --seat a2a-node-local`
- `python exp/push_all.py --auto-sign`

## 验收标准
七步皆有输出；台账与总线各加一条；三面核验 ALIGNED 或如实记不可达。

## 预算
`max_tokens = 2500`（★ 结构性任务（含推导/推算）宜 ≥6000；审阅 4000；其余 2500–3000。★ 若 finish_reason=length 且正文为空，即 think 未闭合 ⇒ 提高预算或简化任务重试。）
