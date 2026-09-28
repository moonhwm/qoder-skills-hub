---
name: fusion-cast-ops
description: "[项目技能] 整合熔铸元技能——把持续问答萃取成卡、正交沉淀入册、外池 LLM 轮铸裁定、四检闸验证的自包含循环（萃-排-铸-验）。触发（满足任一）：「萃取这张卡」「沉淀入册」「轮铸这轮」「测撞注册」「整合熔铸」「fusion cast」；技能创建/修订后要过碰撞与哈希闸登记时；需要判官裁定重算（多数决+版本锚+回滚指针）时；问「这描述撞不撞」「装过的还在不在」时。不触发：单件技能从零锻造主链（N-C-D 三节点）→skill-forge-pipeline；事中额度信号与 Q 档守护→quota-guard-ops；事后报账→quota-ledger-ops。English triggers: fusion cast, extract-deposit-cast-verify, collision gate, verdict recount."
---

# 整合熔铸元技能（fusion-cast-ops）

> 能力域=管理｜输入型=问答日志/技能描述/判官票｜输出型=萃取卡/入册登记/裁定记录/审计判决｜只读性=否（写 registry JSONL）｜依赖=python3 标准库（零凭证）

## 〇、定位与正交性（先划界，再开工）

| 邻席 | 管什么 | 本技能让渡 |
|---|---|---|
| skill-forge-pipeline | 单件技能的 N-C-D 锻造主链与大修模式 | 造单件的方法论全归它；本技能只管**多件循环**的萃取沉淀与轮铸裁定层 |
| quota-guard-ops | 事中额度信号、Q0-Q3 档位 | 信号判定归它；本技能成本帽（C10）只做声明式默认档 |
| quota-ledger-ops | 事前估算与事后报账 | 记账归它；本技能裁定记录可喂给它做阶段账 |

本技能唯一辖区 = **元循环本身**：萃取保真、沉淀正交、轮铸重算、入册验证。

## 一、诚实边界（置顶）

1. 判官的话要重算：裁定永远由 `cast` 子命令按票数重算，不采信任何判官自述的「多数通过」。
2. 「装过≠还在」「静默≠装齐」「配置了≠生效了」——一切注册态以哈希闸实测为准，不靠记忆。
3. 脚本 verdict 文件是裁定唯一事实源；对话里的口头结论不算数。

## 二、四段 workflow（C8 固定：萃-排-铸-验）

### 段 1 · 萃（extract）
输入：问答日志 qa.jsonl（每行 `{"q","a","conf":实证|估算|假设,"about_agent":bool,"verdict":"wrong"?,"why"?}`）。
动作：`python3 scripts/fusion_cast.py extract --qa qa.jsonl --out card.json`
输出：萃取卡（原话透传、conf 分布、top3_wrong、card_md5）。
🔴 检查点：conf 非法→拒；缺 about_agent=true 的本体问答→拒（对齐原始积累不可跳）。

### 段 2 · 排（deposit）
输入：card.json + 归宿域。动作：`python3 scripts/fusion_cast.py deposit --card card.json --registry reg.jsonl --home <域>`
输出：registry 哈希链一行（归宿唯一；同卡同域幂等跳过）。
🔴 检查点：同卡异归宿→拒（沉淀正交检，exit≠0）。

### 段 3 · 铸（cast）
输入：判官票 verdicts.jsonl（奇数≥3）+ 版本锚。票行 schema：`{"judge":<名>,"vote":"better|worse|same","margin":"slight|clear"}`——better/worse 票 margin 必填（缺省拒收，禁向强结论 fail-open）；same 票 margin 可省。version/prev 均须 x.y.z（prev 另许 none）。
动作：`python3 scripts/fusion_cast.py cast --verdicts v.jsonl --version 1.1.0 --prev 1.0.0`
输出：裁定记录（decision=KEEP/REVERT/DRAW + margin + rollback_to 指针，C9）。
🔴 检查点：偶数票或 <3 票→拒裁；REVERT 自动锚 prev 版本为回滚对象。

### 段 4 · 验（register + collide + hashgate + audit）
- 描述入册（descs.jsonl 的唯一出生路径）：`python3 scripts/fusion_cast.py register --name <名> --desc "<描述>" --registry-desc descs.jsonl`——写 {name, desc, desc_md5}，重名即拒。descs.jsonl schema 即此三字段，逐行 JSON。
- 注册前：`python3 scripts/fusion_cast.py collide --desc "<新描述>" --registry-desc descs.jsonl [--threshold 0.3]`（C4：Jaccard≥阈值打回；C6：出 top-3 近邻供澄清。阈值 0.3 的标定依据：同文=1.0、低撞面≈0 的取值中点偏上，0.2-0.4 可调；钳制域 [0.05,0.95]，越界拒收——C4 闸禁被参数整体绕过）。
- 顺序纪律：先 collide 放行 → 再 register 入册。
- 巡检时：`python3 scripts/fusion_cast.py hashgate --name <名> --desc "<现描述>" --registry-desc descs.jsonl`（C2：名实漂移检；注册表重名先修表）。
- 成文后：`python3 scripts/fusion_cast.py audit --skill-dir <目录>`（frontmatter≤1024 含 `>-` 块标量写法/指针可达/自指频度/凭据嗅探）。
🔴 检查点：注册表为空时 collide 拒放行（禁静默过闸）；描述词表 <8（约 4 个 CJK 字以下触发面）拒测并提示补触发词——短名先补描述再来。

## 三、失败模式（if-then 三段式）

1. **若** collide 打回（J≥0.3）→ **则** 改写触发面差异段，重测；两次仍撞→改候选名 → **否则**（放行）登记 desc_md5 入册。
2. **若** cast 判 DRAW（非多数）→ **则** 本轮不 keep 不 revert，delta 减量后重评；连续 2 平局→熔断移交人工 → **否则**按 decision 推进。
3. **若** hashgate 报漂移 → **则** 以注册表为正本，核查安装位内容，登记漂移事件（谁漂、何时、何值）→ **否则**继续。
4. **若** deposit 归宿冲突 → **则** 退回首问归宿映射，禁一卡两域 → **否则**入册。
5. **若** audit 报 AUDIT_FAIL（超长/缺指针/自指名频>40 次/疑凭据）→ **则** 逐项修复后重跑 audit，未过不交付 → **否则**封版。
6. **若** cast 判 REVERT（worse 多数）→ **则** rollback_to=prev 执行回滚，残余登记 FORGE_REPORT → **否则**（KEEP/DRAW）按规推进。

## 四、B 四检闸（每次循环必过）

| 闸 | 检什么 | 机检/人工 |
|---|---|---|
| 路由体检 | 描述偏差、触发词碰撞、名实漂移 | collide+hashgate 机检；语义偏差人工 |
| 整合缺陷 | 副本漂移、循环引用、默认值未审 | audit 机检子集；默认面逐项人工 |
| 萃取保真 | 原话透传、conf 分级、禁摘要改写 | extract 强制机检 |
| 沉淀正交 | 归宿唯一、完备性、缺席即声明 | deposit 机检唯一性 |

## 五、反模式黑名单

| # | 反模式 | 替代做法 |
|---|---|---|
| 1 | 采信判官自述多数 | cast 票数重算为唯一事实源 |
| 2 | 萃取时摘要改写原话 | 原话透传 + conf 三级 |
| 3 | 一卡多域「先都放着」 | deposit 正交检，冲突即退 |
| 4 | 空注册表直接放行测撞 | 禁静默：无基线不判决 |
| 5 | 版本裁定无回滚指针 | C9 版本锚+rollback_to 必填 |
| 6 | 偶数票强行裁决 | 奇数多数决，不足拒裁 |

## 六、自检

```bash
python3 scripts/fusion_cast.py --smoke   # 22 项含 15 负断言（负断言源自判官 bug 清单反用例）；只测 happy path 视为无效
```

## 七、C1-C10 落位表

C1  collide 先过滤（域过滤为人工预筛；注册表≤千席时全量扫描即子集过滤的退化形）｜C2  hashgate｜C3  判官置信 ECE/Brier 验收=人工闸（本版不机检，声明为边界）｜C4  collide 0.3 打回｜C5  触发词雷同性由 collide top-3 人工复核｜C6  collide top-3 输出+低置信转澄清｜C7  top3_wrong 错题本随卡存 card.json，「轮轮重跑」钩子=下轮 extract 的 qa.jsonl 须含前轮 top3_wrong 重测问答（流程纪律，写前自检清单核）｜C8  萃-排-铸-验四段固定｜C9  cast 版本锚+回滚（version/prev 均须 x.y.z 或 prev=none，垃圾值拒收）｜C10  成本帽声明式默认档：默认档=T2 中档（子代理≤2），升档 T3 须先走 quota-ledger-ops 定档判决；数值帽归 quota-ledger-ops

## 八、已知边界

- C3 置信校准（ECE/Brier）本版为人工闸，未机检——判官置信度数据不足时如实声明。
- 语义层路由偏差度量（position/verbosity bias）不机检，归 D 节点判官+人工。
- registry 为单文件 JSONL；并发写不防护（单席纪律外场景勿用）。
- frontmatter 用单引号包 description 时，长度计量含两引号（±2 边缘误伤面在案，建议用双引号或块标量写法）。
- 块标量指示符覆盖 `> >- >+ | |- |+ |2` 等合法 YAML 变体（含缩进指示符），未识别写法跌落裸行提取（长度=指示符本身，自然触发越界拒——fail-closed 方向）。
