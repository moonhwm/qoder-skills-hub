# 排期日期核验政策

## 目录
- 第 1 节 日期信源通道分级
- 第 2 节 上升与核验流程
- 第 3 节 排期 JSONL 契约
- 第 4 节 常见翻车点

> 通道档（C0-C4）、上升等级（T0-T3）、conf 双词表与 Conflict→人工铁律
> 一律引用 source-semantics-sentinel / cross-session-workflow-bridge 的定义，本文件只做排期场景映射。

## 第 1 节 日期信源通道分级

| 通道 | 例子 | 定档 | 日期 conf 上限 |
|---|---|---|---|
| 会议官网 CFP/时间轴原文 | 当届官网 "Important Dates" 页 | C1 | empirical |
| 学会官方通知 | APS/IAEA/IEEE 邮件公告、官方日程 PDF | C1 | empirical |
| 聚合站点 | WikiCFP、CCF  deadline 助手、学术日历聚合、内置 vendor 的 ai-deadlines 快照（`references/data/`） | C3 | assumed（仅作线索） |
| 往届规律外推 | "去年 7 月截止，今年应该也差不多" | C3 | assumed，且必须标 tentative |
| 社媒/群聊截图 | 群通知截图 | C4 | 禁入排期，只作核验线索 |

铁律：进入排期交付物的日期，conf 只允许 empirical/estimated/assumed 三档；
聚合站点与规律外推的日期**永不**标 empirical。

## 第 2 节 上升与核验流程

1. **T0 自动判**：deadline_triage.py 格式校验（日期合法性、conf 词表、必填字段）；
2. **T1 交叉复核**：聚合站日期必须与官网交叉一次；一致才升 estimated；
3. **T2 官网核验**：打开当届官网 Important Dates 页，记录 URL + 抓取日期（data_cutoff）→ empirical。
   官网只有"Coming soon"时：登记月度窗口（"YYYY-MM" 格式）+ conf=assumed + tentative，
   并在排期表注明"待官宣"，禁止把外推日期伪装成官宣；
4. **T3 人工裁决**：官网与聚合站矛盾、官网自相矛盾（两个页面日期不同）→ Conflict 登记，交用户裁决，
   禁止静默二选一。

时区纪律：会议截止常用 AoE (UTC-12) 或本地时区——核验时必须连同时区一起抄录，
写进事件的 `tz` 字段；跨时区换算错误是排期事故高发点，换算结果 conf 降一档。

## 第 3 节 排期 JSONL 契约

```json
{
  "event": "SOFT 2026",
  "domain": "fusion_eng",
  "tier": "核心",
  "deadline_type": "abstract",
  "date": "2026-12-15",
  "tz": "AoE",
  "source_url": "https://...",
  "verify_stage": "T2",
  "conf": "empirical",
  "cycle_note": "两年一届，偶数年"
}
```

- `domain` 建议取值：plasma / fusion_eng / ai / ai4sci / materials / physics_general / domestic；
- `deadline_type`：abstract / paper / registration / workshop_proposal / journal_special 等；
- 顶层包裹：`{"data_cutoff": "YYYY-MM-DD", "events": [...]}`（data_cutoff 必填，不得 null）；
- 与 deadline_triage.py / ics_gen.py 的字段契约保持一致（脚本只认上表字段，多余字段原样透传）。

## 第 4 节 常见翻车点

1. **把"去年的日期"当今年的** → 一切外推标 tentative + assumed；
2. **聚合站日期滞后**（官网已延期，聚合站没更新）→ 一律以官网为准；
3. **摘要 vs 全文截止混淆**（APS 系摘要先行；SOFT 摘要与全文分离）→ deadline_type 分开登记；
4. **workshop 与主会混档** → tier 字段分开标，交付物分开呈现；
5. **时区遗漏**（AoE 与北京时间差 20 小时）→ tz 必填，缺失按 assumed 降档；
6. **期刊特刊截稿遗漏** → 会后专刊作为 journal_special 节点单独登记。
