---
name: forge-round-robin-ops
description: >
  技能轮铸调度官——一批待锻技能的名册登记、能跑门（Phase A 静态可运行性）、轮铸排期（Phase B 完善轮）与裁定回录。
  当用户说「排期轮铸」「轮铸这些技能」「技能排队锻造」「先能跑再完善」「锻造排期」「roster forge」
  「round-robin forge」「一批技能挨个锻」「锻造调度」，或上传多个技能包要求批量改造/大修时触发。
  边界：单件技能怎么锻归 skill-forge-pipeline（主链+短链）管；本技能管「哪批、谁先谁后、谁已能跑、谁待完善、谁已定案」。
  铁律：能跑门全静态（compile≠exec，外来脚本永不执行）；能跑门不过禁入完善轮；roster.json 单一事实源；裁定未回录指针不推进。
  English triggers: "forge roster", "round-robin forging", "schedule skill forging", "runnable first, refine later".
---

# 技能轮铸调度官（forge-round-robin-ops）

> 立法锚：**「先能跑，再完善；门不过，不进轮；裁定不回录，指针不推进。」**

## 定位与边界

- 本技能管**批次级调度**：名册（roster）登记 → Phase A 能跑门 → Phase B 轮铸排期 → 裁定回录，循环至全部 alumni（定案出队）。
- 单件技能的锻造动作（女娲-仓颉-达尔文、短链、外池审判）**归 skill-forge-pipeline 管**——本技能只做排期与状态机，产出「下一件锻谁+为什么」，锻造本身由主代理按管线技能执行后回录。
- 外来脚本**永不执行**（审计只静不动）：能跑门是编译级 `compile()`＋文本级检查，compile 不 exec、读文本不运行。

## 两相教义

| 相 | 名 | 内容 | 出相条件 |
|---|---|---|---|
| Phase A | 能跑门 | 静态六检：源在/SKILL.md 在/frontmatter 合规/相对链接可解/.py 编译级语法/scripts 引用在位 | runnable=true → A-passed |
| Phase B | 完善轮 | 排期取件 → 走 skill-forge-pipeline 锻造 → 裁定（KEEP/REVISE/FAIL）回录 | KEEP → alumni 出队 |

排期优先级：**能跑门未过者绝对优先**（A-pending/A-failed，未检先于已检，失败早候）；全部过门后才进 Phase B，最久未锻者先轮（从未锻过最优先）。细则与 roster schema 见 [references/schedule-doctrine.md](references/schedule-doctrine.md)。

## 工作流（五步循环）

### Step 1 · 建册
`python scripts/forge_roster.py --init <roster.json>`（撞名拒写 exit 2，不覆盖既有名册）。

### Step 2 · 登记
逐件 `--register <roster> --name <kebab-case> --src <目录|.skill|.zip> [--version V] [--note T]`。
自动计算源 md5（目录=相对路径+字节滚 hash）、登记相位 A-pending。同名再登记=换源回炉：A-failed 自动复位 A-pending 待重门，其余相位保留。

### Step 3 · 能跑门 🔴
`--gate <roster> --all`（或 `--name` 单件）。六检全静态；任一不过即 A-failed 并列出失败项，exit 1。
**A-failed 禁入完善轮（硬闸，脚本级）**：先修复源、再登记回炉、重过门。

### Step 4 · 排期
`--next <roster>` → 输出 `next/phase/reason/action`。决策只读名册，不臆测；名册全 alumni 时如实报「全定案」。

### Step 5 · 锻造回录
按 `--next` 指向走 skill-forge-pipeline（新件首锻 N-C-D+短链；既有件大修 D+短链），裁定落定后：
`--advance <roster> --name N --verdict KEEP|REVISE|FAIL --note "轮次纪要"`。
KEEP→alumni 出队；REVISE/FAIL→留 B-rounds 待下轮。**未回录不推进**——`--next` 只认 roster.json。

总览：`--status <roster>`（相位分布/各件轮数/最近裁定/下一件）。自检：`--smoke`。

## 失败模式与降级（if-then）

| 触发条件 | 一线修复 | 兜底 |
|---|---|---|
| 名册不存在/损坏 | 报 exit 3，提示先 --init | 不猜不建空档顶替 |
| 外来技能包脚本"能不能跑"存疑 | 只信六检静态证据 | 判 A-failed 并列出失败项，交人工；永不试跑 |
| A-failed 件被要求直接进完善轮 | 脚本硬闸 exit 3 拒绝 | 无兜底——这是立法 |
| 锻造裁定未落定就想推进 | --advance 须带 --verdict，缺参 exit 2 | 名册不动 |
| 名册全 alumni | --next 如实报「全定案」 | 新件来了重新登记即可 |

## 反模式黑名单

| # | 反模式 | 替代做法 |
|---|---|---|
| 1 | 试跑外来脚本验证"能跑" | 能跑门=compile+文本检查，零执行 |
| 2 | 门未过先完善（镀金废墟） | 先能跑硬闸，A-failed 禁入轮 |
| 3 | 凭记忆/口头推进排期 | roster.json 单一事实源，--advance 回录才推进 |
| 4 | 一次锻多件赶工 | 轮铸：一轮一技，最久未锻优先 |
| 5 | 定案件反复重锻 | KEEP 出队 alumni；重开须换源再登记 |

## 自检

`python scripts/forge_roster.py --smoke` —— 合成夹具：门六检正反断言（语法坏件/悬空链接/缺 description/坏 zip 全拦下）、**compile≠exec 铁律自证**（模块顶层 raise 的脚本过门且未被执行）、包件过门、排期优先级、A-failed advance 硬闸、换源回炉复位。PASS 字样为凭。

## 产物指针

- 脚本：`scripts/forge_roster.py`（纯标准库，--init/--register/--gate/--next/--advance/--status/--smoke）
- 名册：`<roster.json>`（单一事实源；相位 A-pending/A-passed/A-failed/B-rounds/alumni）
- 细则：`references/schedule-doctrine.md`（六检明细、schema、排期算法、与 skill-forge-pipeline 接口）
