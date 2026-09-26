# verifier v2 验收标准 —— 碎片垃圾清理（semantic-oncology-ops 运维）

> 目标口令：「清理目前已有碎片及垃圾。」（extension skill: semantic-oncology-ops）
> 与 v1 关系：v1 测退休工程六线；v2 测本次清理的彻底性、安全性、留痕完整性。不复用不覆盖。

## 判据

| 编号 | 判据 | 通过条件 |
|---|---|---|
| C1 | Tier-1 删除彻底 | manifest 27 项目标全部不存在于磁盘 |
| C2 | 复扫零残留 | 复扫无 .converted.md、无 0 字节文件、无 _tmp 中间产物（白名单：verifier/runs 内日志、双保险镜像、.bak 法定备份） |
| C3 | 台账健康 | 交割台账.json / 计时器任务台账.json / 额度状态台账.json 可解析；两条 JSONL 零坏行 |
| C4 | 报告落盘 | 《碎片垃圾清理报告_v1.0_20260902.md》存在于 registry，且含四件套结果（冗余扫描/INDEX核对/台账健康/文件垃圾）与三层分级 |
| C5 | 母本完整 | 全部被删 .converted 对应母本 .md 仍存在且非空 |
| C6 | 零明文凭证 | 本次新产出文件（报告+manifest+criteria）七项秘密零命中（继承 v1 V8 铁律；check.py 本体豁免——SECRETS 以其为唯一载体，v1 先例） |
| C7 | 安全边界 | 删除集合 ⊆ Tier-1 白名单（.converted/空文件/_tmp），未触碰双保险镜像、.bak 备份、任何 ledger/INDEX/锚链文件 |
