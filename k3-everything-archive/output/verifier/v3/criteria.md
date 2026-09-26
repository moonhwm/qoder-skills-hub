# verifier v3 验收标准 —— 未完工作批次（INDEX 重建 + 台账小修）

> 目标口令：「请您继续回顾并进行手头没完成的工作」本轮切片：INDEX v2.0 重建＋额度台账 schema 对齐＋计时器台账格式统一。
> 与 v1/v2 关系：v1 退休工程六线、v2 碎片清理；v3 测索引与台账修复的正确性。

| 编号 | 判据 | 通过条件 |
|---|---|---|
| D1a | INDEX 全覆盖 | registry 根目录每个文件（除 INDEX.md 自身）均在 INDEX.md 出现 |
| D1b | INDEX 零幽灵 | INDEX 列名逐项在磁盘存在（子目录行除外） |
| D2 | 额度台账 schema | 含 current_level＋updated_at；tier==current_level=='Q1'；JSON 可解析 |
| D3 | 计时器台账格式 | 13 条任务全部含「任务名」字段；JSON 可解析 |
| D4 | 零明文凭证 | INDEX.md 与两台账七项秘密零命中 |
