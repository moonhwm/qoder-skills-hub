# 留痕与 AI 读者通知协议（change-notice protocol）

> 目标读者：后续再读取被修改文件的 AI agent（k3 / k3 集群等）。
> 原则：**任何审计驱动的直接修改，必须三件套齐全**——文头留痕块 + CHANGELOG 行 + k3 通知 JSONL。
> 自动化入口：`scripts/notice_stamp.py`（幂等，可重复盖章更新块）。

## 1. 文头留痕块（AI_READER_NOTICE）

**按文件类型分派注释格式**（由 `scripts/notice_stamp.py` 自动执行，手写时须严格对齐）：

| 文件类型 | 块格式 | 插入位置 |
|---|---|---|
| .md / .txt / .html | `<!-- AI_READER_NOTICE ... -->` HTML 注释块 | 文件最前，先于标题 |
| .py / .sh / .yaml / .yml / .toml | `# AI_READER_NOTICE` 起、`# END_AI_READER_NOTICE` 止的 `#` 行块 | .py/.sh 跳过 shebang 与 PEP263 coding 行之后（注释非语句，不破坏可执行性） |
| .tex | `% AI_READER_NOTICE` 起、`% END_AI_READER_NOTICE` 止的 `%` 行块 | 文件最前（含 `\documentclass` 之前；`%` 注释不破坏编译） |
| .docx / .pdf / .json 等 | **不写块**（会破坏格式），只登记 CHANGELOG + JSONL | — |

机器可读字段固定（两种格式相同）：

```
change_id: CHG-YYYYMMDD-###
date: YYYY-MM-DD
agent: <执行者，如 k3-worker-1>
reason: <修改原因（必须含审计问题编号，如 S1/P2/CF-3/DORM-1）>
audit_ref: <审计报告绝对路径>
summary: <一句话摘要>
notice_to: 后续读取本文件的 AI agent（k3 / k3 集群等）——引用前先核对 audit_ref。
```

规则：
- 同一文件重复修改 = **更新**该块（change_id 递增），历史去向 CHANGELOG 查；旧式 HTML 块在 .py 中由脚本自动迁移为 `#` 行块。
- 旧块识别与迁移语义（v1.8 钉死）：脚本按扩展名优先匹配对应注释样式（如 .py 先跑 `#` 分支；`#` 块未命中且文件确含 HTML 块起始标记时才迁移 HTML 块）；**BEGIN 存在但 END 未找到（未闭合/被截断的旧块）时不删除任何内容**，stderr 出 WARNING「未闭合留痕块，未迁移，请人工核查」，新块照常前插——文件会暂时同时含新旧两处 BEGIN 标记，须人工清理残留后重盖。HTML 分支 END 查找限 4KB 窗口内（正常块 << 4KB），未闭合块不会吞掉远处正文。
- 留痕不得破坏可用性：.py 盖章后必须通过 py_compile（脚本内置自检+回滚）；手写留痕者自行验证。
- change_id 顺序号由主代理集中分配（或加实例后缀），禁止并发实例各自编号。
- **change_id 内嵌日期（CHG-YYYYMMDD-…）必须与块内 `date` 字段一致**（即盖章当日）；checker 对不一致输出 WARNING（不阻断，但两实战案例曾 6/6 条全部错位，属留痕质量问题）。

## 2. CHANGELOG（文件级）

- 默认路径：被改文件同目录 `CHANGELOG.md`；表格行：`| date | change_id | file | reason | audit_ref | agent |`。
- 只增不改（append-only）；禁止改写历史行。

## 3. k3 通知日志（集群级）

- 默认路径：被改文件同目录 `k3_notices.jsonl`，每行一条 JSON：
  `{"change_id","date","file","reason","audit_ref","agent","summary","notice_to":["k3","k3-cluster"],"stamped":bool}`。
- k3 集群调度器可订阅该 JSONL 做增量失效处理；字段名冻结，新增字段只允许追加。

## 4. 通知语义约定

- `notice_to` 固定含 `k3` 与 `k3-cluster`；其他读者另加。
- `reason` 必须含审计问题编号（P#/S#/CF#/DORM-#），使 k3 agent 可反查审计报告定位上下文。
- 修改完成后，主代理在交付摘要中列出全部 change_id 清单，作为本轮会话级通知。

## 5. 反例（禁止）

- 只改文件不留痕 → 视为未修复（convergence-loop 纪律 2）。
- 留痕块写「优化了文档」类空话，无 audit_ref → trace 角色判 high。
- 直接覆盖 CHANGELOG 历史行 → trace 角色判 blocker。
- **虚假关闭：reason/summary 写了未落盘的修改 = 勘误级事故**（实战案例2 B2-002 实例：声称三字典字段级 conf 已补，实测仅一处落盘，骗出 CONVERGED 被 grader 抓获）。处理：须走自修正流程——真实补落修改 → 以新 change_id 重盖三件套，reason 注明「勘误补落」及对原 change_id 的更正声明；历史行/历史块不改（append-only），并在 findings 中为该条目补 verify 规范供 `--verify-evidence` 机器复核。
