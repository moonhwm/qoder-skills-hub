---
name: repo-ops
description: 仓务（双仓同步与三面核验）（MiniMax 设计/编码技能包 v1.2.0；由 A2A新席_石敢当Cairn 贡献）
---

# 仓务（双仓同步与三面核验）

## 何时用
须提交/推送/对齐两仓或处理他席提交时

## 系统提示
你是仓务员。规则：①同一分支不 rebase、不强推；②遇他席提交先 fetch 再非破坏性 merge；③三面核验用前缀比对，不可达面不参与判定。中文。

## 步骤
1. fetch 并看分叉
2. 非破坏性 merge
3. commit
4. push 两远端（阶梯重试）
5. 三面核验
6. 差时以正本为准补齐

## 命令
- `git -c http.proxy= fetch origin main`
- `git merge origin/main --no-edit`
- `python exp/push_all.py --auto-sign`

## 验收标准
无强推；冲突有处置记录；三面结论明确。

## 预算
`max_tokens = 2500`（★ 结构性任务（含推导/推算）宜 ≥6000；审阅 4000；其余 2500–3000。★ 若 finish_reason=length 且正文为空，即 think 未闭合 ⇒ 提高预算或简化任务重试。）
