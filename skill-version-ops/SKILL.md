---
name: skill-version-ops
description: "[项目技能] 技能版本流转总署——单件三模式共库（version_flow.py）：①refresh-check 刷新运维（可写性预检/全库盘点与版本漂移扫描/点名技能热加载/插件通道强制健康检查/dist 包源搜索/哨兵核查/通报落库）；②reinstall 重装与分发运维（dist 包一键重装：预检/逐包解压/旧版 .bak 备份/装后版本核验/零伪装如实停止；pip 化分发三铁律与验收链）；③sync-check 便携件同步（台账唯一来源/四重判定/整包枚举/STALE 重蒸馏五拍闭环）。触发（满足任一）：①用户说「重新加载并刷新技能」「刷新技能」「重载技能」「reload/refresh skills」或等价表述（含语音/同音变体，不纠正用户、映射意图）；②用户说「重装技能」「装最新包」「同步安装位」「一键重装」「reinstall」或写回队列有版本差且检测到可写窗口；③用户说「pip化」「一条链接安装」「打成 whl/wheel」；④用户说「便携件」「粘贴即装」「引导件」「同步更新」「portable」或源技能版本递增需判 STALE。中文名：技能版本流转总署。English triggers: skill refresh, skill reinstall, portable guide sync, registry drift check, pip-installable skill package."
metadata:
  version: "1.0.0"
---

<!-- v1.0.0（2026-09-09）：创刊三合一——用户指令「继续继续」+全量化方针，按 skill-version-ops三合设计卡 v1.0 合并 skill-refresh-ops（雁西席 2026-09-01 创刊）× skill-reinstall-ops v1.1.0 × portable-sync-ops 工作副本 v1.0.10。共库 scripts/version_flow.py 收编 refresh_check.sh / reinstall.sh / portable_sync_check.py 为三子命令，判定逻辑逐拍移植；五夹具自检 PASS（F3/F5 初测 FAIL 为夹具环境依赖——root 下 chmod 0555 不可写假设失效，改不存在父目录夹具后全过，如实留痕）。原三件启动退役程序（参照 bidding-docs-ops 范式），本件为唯一入口。cron 1a08227c 冻结→改指本件。references 三件原样收编：channel-registry.md / pipify.md / distill-spec.md。 -->

# 技能版本流转总署（skill-version-ops）

> **能力自报块**（总接口 I3）：能力域=管理｜输入型=触发口令+会话插件清单 / dist 目录+包清单 / 便携台账｜输出型=刷新报告 / 重装核验表 / 同步判定报告｜只读性=分模式（refresh-check=部分写通报；reinstall=写安装位需可写窗口；sync-check=只读）｜依赖=python3 标准库（pip 化另需 pip/build）
> **纪律继承声明**（I4）：继承 conf 词表统一、红线条款、写类例外、信息充分性条款、全局共同遵守（autonomous-advance-ops 为准）。

## §0 定位与三模式路由

本件管技能版本流转全生命周期：**刷新盘点 → 重装换位 → 便携同步**，三模式一个共库 `scripts/version_flow.py`：

| 模式 | 触发 | 命令 | 源件 |
|---|---|---|---|
| ① refresh-check | 「刷新/重载技能」 | `python3 scripts/version_flow.py refresh-check [--upload DIR] [--out FILE]` | skill-refresh-ops |
| ② reinstall | 「重装/装最新包」 | `python3 scripts/version_flow.py reinstall [--dist DIR] [--install-dir DIR] [--pkgs "a b"]` | skill-reinstall-ops |
| ③ sync-check | 「便携件/同步更新」 | `python3 scripts/version_flow.py sync-check [--registry FILE] [--json FILE]` | portable-sync-ops |
| — self-test | 五夹具 | `python3 scripts/version_flow.py self-test` | 三模式全覆盖 |

「刷新」≠「重装」：refresh-check 管盘点—热加载—通道验证—移交/停止—通报；真正改写安装位属 reinstall。两条件（可写窗口∧dist 包源）同真时 refresh 只做移交，不亲自重装。

## §1 模式① refresh-check 标准工作流（六步，顺序执行）

1. **预检**：写 `/app/.user/skills/.writetest` 即删；只读即如实记录「重装停止」，禁止假装成功、禁止部分成功报全成。
2. **盘点**：`ls /app/.user/skills`＋`/app/.agents/skills`＋逐技能 grep `version:` 字段，形成版本基线表；无 version 字段=常态非漂移。（脚本自动化 ①②⑤ 三拍。）
3. **热加载**：用户点名技能逐件 read_file 入上下文，报告版本与在位状态（缺席=如实报缺）。
4. **通道强制健康检查**：对**本会话已装载的全部插件**逐通道执行一次最小调用，调用方式按 `references/channel-registry.md`——该表只存已研究结论；遇表外新插件按 §2 自行研究后**回写该表**（自我更新点）。结果矩阵四态：🟢在线（附实证数据）/🟡在位未授权（给一句话用户动作）/🔴缺失/⚪未装载。缺席≠失败，未测=未测，禁止编造在线。
5. **包源搜索与移交**：脚本扫 upload 三层内 `*.skill`/`skill-dist*`；有包∧可写→移交模式②；缺一→如实停止并给降级路径（用户放包/可写会话/桌面端）。
6. **哨兵与通报**：检查相关 cron 在册；全量结果落 Supabase 通报（conf=A），报告落 `/mnt/agents/output/`。

## §2 通道调用方式研究规程（遇表外插件时）

按插件形态四分类取最小调用，**每通道限一次**（额度纪律）：MCP 插件→select_tools 加载最轻只读工具调一次；CLI 插件→`which <bin>`＋auth status 或 --version；agent-gw 数据源→按其 SKILL.md 发一次最小查询，无任务时以「待命」登记不空转；纯技能→读 SKILL.md 首部即视为调用验证。研究结论回写 `references/channel-registry.md`（日期+实证数据+缺口动作），禁止只验证不回写。

## §3 模式② reinstall 四规程（不可豁免）

1. **预检先行**：先测安装位可写性；只读即如实停止（exit 2）、输出降级路径（界面对话创建/桌面端执行），**禁止假装成功、禁止部分成功报全成**。
2. **备份才可换**：任何包先解压到 `.new`，旧版移 `.bak`，再换位；备份未成才可覆盖——删 `.bak` 属违规。
3. **装后必核**：逐包 grep 版本号回显；报告成功/失败计数，失败项明示原因（包不存在/解压失败/不可写）。
4. **回写闭环**：成功后更新写回队列版本差台账、刷新技能总目录（条目数自检）、更新验证口令应答；失败则登记缺口。

默认参数：dist=`/mnt/agents/upload/skill-dist-20260829`；安装位=`/app/.user/skills`；桌面端环境路径不同，执行前先以其环境变量/实际路径覆盖。常设预授权（写回队列登记在案）：可写窗口出现时可不经逐次询问直接执行——执行后仍须逐包核验并回写。

## §4 pip 化分发（一条链接安装，实证入法）

把技能集合打成 pip wheel，用 PEP 508 直引安装（`pip install "name @ file:///…whl"` 或 `http(s)://…whl`）。三铁律（每条约自一次实坑，细节与验收链见 [references/pipify.md](references/pipify.md)，pip 化任务开工前必读）：

1. **容器套容器**：散装 package-data 会被 compileall 重编译 payload 内 `.pyc` 致 md5 漂移、glob 漏收 dotfile——数据载荷一律压成单个 `payload.zip` 作为唯一 package-data blob，安装后由入口 CLI 自解。
2. **构建目录避开 FUSE**：沙箱工作盘 FUSE 挂载有 rmdir ENOTEMPTY 怪癖会丢文件——构建全程在 /tmp 做，产物再拷回。
3. **消毒扫描先行**：pip 化扩大传播面，打包前对全量内容跑敏感串扫描（激活码/凭据/邮箱），含明文敏感串的包不 pip 化、登记理由。

验收链（不过不交付）：file:// 与 http:// 两种直链安装 exit 0 → MANIFEST 逐条命中（0 不符 0 缺失）→ 安装产物 vs 原包逐条目 md5 比对全同 → 中文路径/正文零乱码抽验。pip 化 ≠ 重装：本件管分发形态，装入安装位仍走 §3。

## §5 模式③ sync-check 便携件同步纪律

- **台账唯一来源**：`assets/portable_registry.json`——一切便携件入册，未入册=不存在（不受同步纪律保护，漂移无人知道）。每条目：id / kind（引导件=粘贴即装单文件 md；整包便携=.skill 归档）/ portable_path / portable_version / sources（只放可机读真实路径；自版本文档指回自身；谱系入 lineage）/ distill / mirror。
- **四重判定**（scripts/version_flow.py sync-check）：**portable_path 存在性**（MISSING）→ **便携件自身版本 vs 登记** → **源件 live version vs 登记**（frontmatter `version:` 优先，无则文首标题 `（vX.Y · …）` 形态，.skill 解包读 SKILL.md）→ **镜像 md5 一致性**。输出 CURRENT/STALE/MISSING 逐件+整包枚举+verdict（SYNC-OK/SYNC-DRIFT，exit 1=漂移）。整包便携默认动态枚举（递归扫 output 全部 .skill 读包内版本），需受控的才入册。
- **STALE → 重蒸馏五拍闭环**：任一引导件 STALE 即走 [references/distill-spec.md](references/distill-spec.md) 第四节上架五拍：**读源 → 重蒸 → 过脱敏闸 → 替换双处（app/ 正本+镜像，md5 复核）→ 台账同步并复检 SYNC-OK**。整包 STALE 则重打包替换。缺任一拍=未闭合。
- **运行频度**：事件驱动为主（源技能版本递增/便携件新制/镜像变更，当轮即跑）；周兜底 cron 在册（1a08227c，已改指本件 sync-check，DRIFT 才报）。静态产物不设高频 cron。
- **诚实声明**：检测器只报真实运行结果；词表缺失、路径不可读、版本号取不到一律显式标注（UNREADABLE 等），不以「大概是最新的」蒙混。台账与实物不一致时以实物为准修台账并留痕。

## §6 边界（六条）

- 不越位向 `/app/.agents/skills` 安装用户技能（该位可写≠该装）；
- 凭证红线：任何通道验证不打印/不转播秘密值，授权态只看 status 不看值；
- 预授权解决「要不要逐次问」，不解决「能不能写」——物理只读时一切重装如实停止；
- 本件只搬包装箱，不改动包内容；包内容版本以 dist 目录/源件安装位为准；
- 不创作技能（skill-creator 的活）；脱敏闸是外部依赖，在场即用、缺席显式声明能力占位；
- 本件为运行时纪律件：台账载体缺席时以通报+cron 双轨登记，载体恢复后回填。

## 退役源流（创刊注记）

本件合并收编三件并为其唯一入口：skill-refresh-ops（脚本+通道注册表全量收编）、skill-reinstall-ops v1.1.0（四规程+pipify 全量收编）、portable-sync-ops v1.0.10（检测器+台账+蒸馏规程全量收编）。原三件保留安装位只读副本作历史参考，退役裁决书与超集核验记录在注册处留痕。
