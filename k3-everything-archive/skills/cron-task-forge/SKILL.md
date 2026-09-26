---
name: cron-task-forge
description: "[项目技能] 定时任务（cron/提醒/自检任务）的创建、审计与降频规范。当用户要求创建/修改/暂停/删除定时任务、定时提醒、每日/每周自检、凌晨自检、月度监测，或审计现有定时任务的成本与必要性时使用；任何其他技能要内嵌定时行为（如每日自检、周期复核）时必须先读本规范。触发词含语音变体：corn/cro/cron 任务、定时任务造卡、任务卡体检。核心交付：任务卡七段式模板 + 必要性定频规则 + card_linter.py 确定性体检（措辞与调度一致/反幻觉条款/异常条款/字符上限）。中文名：定时任务考官"
metadata:
  version: "1.0.0"
---

# 定时任务考官（cron-task-forge）

定时任务卡的**创建规范 + 确定性体检器**。标本来源：「花未眠·凌晨四点自检」任务卡全文（2026-08-29 用户提供）+ 同日的撞车/降频/措辞漂移三轮实证教训。

## 创建流程（新建任何定时任务前按序执行）

0. **先盘点，后创建**：任何 cron 增删改前必须先 `list_cron_jobs` 全量盘点——同项目同主题的既有任务优先复用/合并，禁止撞车（实证：未盘点即注册导致与「花未眠」重复）。
1. **必要性定频**：按失效模式定频率，不按感觉。时敏信号（盯盘/抢券）才可每日；静态产物（代码包/台账）事件驱动 + 每周/每月兜底。决策表见 [references/necessity_rubric.md](references/necessity_rubric.md)。**频率每高一档，额度成本翻倍级增长——先算舰队总账**（Σ 频率×单次消耗），quota 窗口期（额度不足徽标/加油包提示）一律暂停新增。
2. **七段式写卡**：按 [references/card_template.md](references/card_template.md) 填槽——①ls 锚点核验清单（绝对路径）②状态核验（git/VERSION）③快速测试门禁+环境重建降级路径 ④挂账到期检查（带日期/触发条件）⑤双保险落库+状态板更新 ⑥反幻觉条款（只汇报磁盘核验为真，缺测即标缺测）⑦异常如实报告+修复路径。纯检索类任务可省②③，但①⑥⑦不可省。
3. **平台约束**：名称 ≤50 字、正文 ≤8000 字（Kimi UI 实测）；cron 五字段；设过期时间防永久挂账。其余实测约束见 [references/platform_notes.md](references/platform_notes.md)（update 是整体替换、暂停≠删除、提醒绑定会话、额度不足徽标语义）。
4. **过检才注册**：写完后必须跑 `scripts/card_linter.py --name "任务名" --cron "表达式" <卡文本>`，PASS 才允许 `add_cron_job`；FAIL 逐项修复复检。

## 审计/改卡流程

- **改正文前先存档原文**——`update_cron_job` 对正文是**整体替换**，服务端全文不可全读（列表只给截断前缀），盲改会丢看不见的部分（ERR-FAL02-01 实证）。拿不到全文就只改 `cron_expr`/`status`/`title`，正文等全文到手再动。
- **措辞与调度必须一致**：正文「每日」↔ cron 必须 daily；降频后正文频率字样同步改（lint C4 硬判）。
- **暂停优先于删除**：不再需要的任务先 `status=paused`（内容保留、一句话恢复），确认无用一个周期后再删。

## 给其他技能的强制条款（skill 创建流程必读）

任何技能若内嵌定时行为（每日自检/周期复核/到期提醒）：
1. 必须随技能附带可独立运行的检查脚本（纯标准库优先），任务卡只写「跑脚本 + 全绿静默 /  FAIL 报告」，把细节沉进脚本而非卡正文；
2. 任务卡文本必须过 card_linter.py；
3. 频率必须过必要性定频表，并在技能正文写明定频理由。

## Resources

- `scripts/card_linter.py`：任务卡确定性体检（C1 名称长度 / C2 正文长度 / C3 cron 合法 / C4 措辞调度一致 / C5 反幻觉条款 / C6 异常条款 / C7 绝对路径 / C8 挂账带期 / C9 身份标签 / C10 重建降级加分项）；`--self-test` 内置五正反夹具。
- [references/card_template.md](references/card_template.md)：七段式模板 + 花未眠标本全文 + 收敛版周检实例。
- [references/necessity_rubric.md](references/necessity_rubric.md)：失效模式×频率决策表 + 舰队成本模型（含额度估算口径与实测校准规程）。
- [references/platform_notes.md](references/platform_notes.md)：Kimi 定时任务平台实测约束与语义陷阱表。
