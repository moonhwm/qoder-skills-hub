# FORGE_REPORT · fusion-cast-ops（整合熔铸元技能）

锻造管线：skill-forge-pipeline v2.4.1（首锻 N-C-D + N⇄D 短链）｜日期：2026-09-23｜终版：**v1.2.1**

## 一、主链纪事

- **N（女娲）**：从 forge-research 研究线三切片（研究简报/撞合原型模/双节点螺旋轮铸设计卡）提炼——核心方法论一句话「路由先过滤子集再选择，熔铸固定萃-排-铸-验四段，判官票数重算为唯一事实源」；反模式黑名单 6 条；诚实边界 3 条。🔴 N 准出三项齐。
- **C（仓颉）**：SKILL.md 必备件全落（frontmatter 375 字符、四段 workflow、if-then 6 条、🔴检查点 4 处、黑名单专章、自检命令、Runtime 中立）。C4 注册测撞 vs 345 席注册表 maxJ=0.075（<0.3 放行）。
- **D（达尔文）**：前置闸核全件 → spawn 3 独立判官（结构/实证/对抗用户）→ **3×REVISE**；P1×6（audit `>-` fail-open、REVERT margin 不对称、registry 输入面断裂、<8 tokens 未文档化、/tmp 矛盾、docstring 虚称）+P2×9。实证席以 1200 字符块标量测试坐证 fail-open。

## 二、短链纪事（票数全登记）

| 轮 | delta | paired 票（结构/实证/对抗） | 裁定 |
|---|---|---|---|
| R1 | v1.0.0→v1.1.0：P1 六项全修+smoke 11→18 项 | better/slight/KEEP；better/slight/REVISE；better/slight/KEEP | KEEP，margin=slight（第 1 轮 slight） |
| R2 | v1.1.0→v1.2.0：D-1 空行截断、D-2 缺 lhash、P2-1..4 全修+smoke 18→21 | better/slight/KEEP ×3 | KEEP，margin=slight（**连续 2 轮 slight → 出链判据①触发**） |
| 补漏 | v1.2.0→v1.2.1：判官残余可机修项清零（`>+/|2` 变体正则、非法 vote 带票号、docstring prev none、文档三同步）+smoke 21→22 | 未派整轮判官（出链后 micro-delta，验证=机检闸） | 机检全绿封版 |

## 三、流程缺陷与诚实声明

1. **短链第 0 动漏建 .bak**：v1.0.0 快照未建于 delta 前，实体不可逐字恢复。R1 paired 锚点降级为「前轮评审单摘要+delta 清单」，已在 R1 证据包向三判官明示；v1.1.0/v1.2.0/v1.2.1 三件 .bak 已补链。
2. **前轮逐项 9 维分部分佚失**（会话裁剪）：R1 复评 prompt 以可核 P1/P2 清单替代 top3 摘要，登记在案。
3. **edit_file 两度静默未落**：段5/6/7 与 audit 正则 edit 报成功实未改，均被改必验闸 grep 抓包重打（宣称-实证差 2 起，已随验证输出修复）。
4. R1 判官的话全部重算后采信（dogfood：判官指认逐条复现确认后才入 delta）。

## 四、终版验证证据（改必验闸，输出原文可复跑）

- `python3 -m py_compile` rc=0
- `--smoke` **22/22 PASS（含 15 负断言）**：负断言全部源自判官 bug 清单反用例（conf 非法/缺本体问答/归宿冲突/缺文件/重名/同文测撞/短描述/漂移/偶数票/块标量超长/链篡改/空行绕过/缺 lhash/缺 margin/块标量变体）
- `audit --skill-dir .` 自审 PASS（375 字符 description、零凭据嗅探命中）
- 阶段 verifier v2 **14/14 PASS**（账本链/PLAN/证据六件/frontmatter/黑名单/诚实边界/C1-C10/compile/smoke/collide maxJ=0.075/audit/零凭据），runs/ 日志 4 跑在案
- 判官对抗复测摘录：1024/1025 双写法边界精确；threshold 0.05/0.95 精确；`>+` 1200 字→rc=5；影子行→「第 N 行缺 lhash」；合法链字段重排/unicode 重写不误伤

## 五、残余登记（出链判据①径，全部非阻断项）

| # | 残余 | 级 | 处置状态 |
|---|---|---|---|
| R-1 | 非 dict JSON 行（如 `[1,2,3]`）混入时 4 条命令抛裸 traceback（rc=1 但非指人话） | P2 | 在案未修——类型层兜底留待下轮 |
| R-2 | same 票 margin 不校验（垃圾值放行，无语义危害） | P3 | 口径声明已补 SKILL 段3 |
| R-3 | 单引号 description 长度含两引号（±2 边缘误伤） | P3 | 已知边界登记（§八），建议双引号/块标量 |
| R-4 | C7「轮轮重跑」为明文流程纪律，无机制钩子 | P3 | 落位表明文化，软约束如实声明 |
| R-5 | C3 置信校准（ECE/Brier）人工闸未机检 | 边界 | §八声明 |
| R-6 | 语义层路由偏差不机检（归 D 节点判官+人工） | 边界 | §八声明 |
| R-7 | 并发写不防护（单席纪律外勿用） | 边界 | §八声明 |

## 六、已知边界（总）

纯标准库零凭证；registry 单文件 JSONL；collide 阈 0.3 标定依据在 docstring（0.2-0.4 可调，钳制 [0.05,0.95]）；C10 数值帽归 quota-ledger-ops；触发词误吸的语义层归人工/判官。

## 七、产物清单

- `SKILL.md`（终版 v1.2.1 配套）+ `scripts/fusion_cast.py` v1.2.1（22 项 smoke）+ 本报告
- .bak 链：v1.1.0 / v1.2.0 / v1.2.1（paired 棘轮基准）
- paired 证据包：paired_round1/delta_and_prior_reviews{,_r2}.md
