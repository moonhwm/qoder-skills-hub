---
name: portable-sync-ops
description: "[项目技能] 便携件同步总署——一切「粘贴即装」引导件与整包便携（.skill）的登记台账与同步更新纪律。触发（满足任一）：①用户说「便携件」「粘贴即装」「引导件」「异模型能用吗」「便携化」「同步更新」「portable」或等价表述（含语音变体，不纠正用户、映射意图）；②要把某个技能做成无技能系统模型可用的单文件引导件时；③源技能版本递增后需判断便携件是否过期（STALE）并重蒸馏/重打包时；④交接镜像与正本一致性核验时。覆盖：便携件登记台账（assets/portable_registry.json，未入册=不存在）、同步检测器（scripts/portable_sync_check.py：存在性/版本漂移/镜像 hash/整包枚举）、蒸馏规程（references/distill-spec.md：人工骨架模式/私藏层剔除/上架五拍）、STALE→重蒸馏五拍闭环。不覆盖：技能创作本身（走 skill-creator）、脱敏闸本体（走 output-verdict-gate/release-gate-audit）。中文名：便携件同步总署。English triggers: portable guide sync, paste-to-install bootstrap, cross-model portable distill, registry drift check."
metadata:
  version: "1.0.6"
---

# 便携件同步总署（portable-sync-ops）

<!-- v1.0.0（2026-09-08）：创刊。用户指令「做出目前便携件，连同以往便携件进行能够同步更新的相关设置固化」。首日实战：检测器首检即捕获 persona 源技能 1.2.0→1.3.0 漂移 + 镜像缺两件引导件，按五拍重蒸馏闭合，全链 SYNC-OK。 -->
<!-- v1.0.1（2026-09-08）：台账 v1.2 入册 eastmoney-rumor-sentinel（整包便携首件受控件，sources 指 skill-work 工作副本）；工作副本落位 skill-work/portable-sync-ops（/tmp 易失实证，耐久层自此为准）。 -->
<!-- v1.0.2（2026-09-09）：核查演练轮——A 组实检捕获 persona 源 1.3.0→1.4.0 漂移（安装位第二连中），按五拍重蒸馏 v1.4.0-portable 闭合（体积 10148B 守 ≤10KB 契约）；阳性对照（毒化台账 0.9.0）正确报 STALE；台账 v1.3。 -->
<!-- v1.0.3（2026-09-09）：台账 v1.4 跟升 eastmoney-rumor-sentinel 1.1.0（正文扩版轮）；教训入册：打包前必清 __pycache__（pyc 两回混入），distill-spec §四上架五拍第 3 拍增补「清缓存」注。 -->
<!-- v1.0.4（2026-09-09）：台账 v1.5 跟升 eastmoney-rumor-sentinel 1.2.0（全量正文令+反爬识别轮：东财「身份核实」验证页实测，ChannelBlocked 报障不报零）。 -->
<!-- v1.0.5（2026-09-09）：台账 v1.6 跟升 persona-iteration-loop-ops 1.5.0（双线合并轮：A线1.4.0×B线I9-1.0.4 碰撞合并+§11 直述层训练场；引导件跟升 1.5.0-portable 10,238B 达标）。 -->
<!-- v1.0.6（2026-09-09）：台账 v1.7 跟升 K3-BOOTSTRAP v1.1（函件复活第一义务节植入，机主立法轮）。 -->




## §0 定位

- 本件管**便携件的生命周期**：登记 → 同步检测 → 过期重蒸馏/重打包 → 双处替换 → 台账闭合。
- 便携件两类：**引导件**（单文件 md，全文粘贴即激活，供无技能系统的异模型）与**整包便携**（.skill 归档，下载再分发）。
- 边界：不创作技能（skill-creator 的活）；脱敏闸是外部依赖，在场即用、缺席显式声明能力占位。

## §1 台账唯一来源（assets/portable_registry.json）

- **一切便携件入册，未入册=不存在**（不受同步纪律保护，漂移无人知道）。
- 每条目：id / kind / portable_path（正本）/ portable_version / sources（**只放可机读真实路径**；自版本文档指回自身；谱系说明入 lineage 字段）/ distill / mirror（镜像路径）。
- 整包便携默认**动态枚举**（检测器递归扫 output 目录全部 .skill 读包内版本），需受控的才入册。

## §2 同步检测（scripts/portable_sync_check.py）

```bash
python3 scripts/portable_sync_check.py --registry assets/portable_registry.json --json report.json
python3 scripts/portable_sync_check.py --self-test   # 三夹具：CURRENT/STALE/MISSING
```

- 四重判定：**portable_path 存在性**（MISSING）→ **便携件自身版本 vs 登记** → **源件 live version vs 登记**（frontmatter `version:` 优先，无则文首标题 `（vX.Y · …）` 形态，.skill 解包读 SKILL.md）→ **镜像 md5 一致性**。
- 输出：CURRENT / STALE / MISSING 逐件 + 整包枚举清单 + verdict（SYNC-OK / SYNC-DRIFT，exit 1=漂移）。
- 纯标准库；报告如实写，禁编造同步结果。

## §3 STALE → 重蒸馏五拍（闭环纪律）

任一引导件 STALE，即走 [references/distill-spec.md](references/distill-spec.md) 第四节上架五拍：**读源 → 重蒸 → 过脱敏闸 → 替换双处（app/ 正本+镜像，md5 复核）→ 台账同步并复检 SYNC-OK**。整包 STALE 则重打包替换。缺任一拍=未闭合。

## §4 运行频度（继承 cron-task-forge 纪律）

- **事件驱动为主**：源技能版本递增 / 便携件新制 / 镜像目录变更，当轮即跑检测。
- **周兜底**：每周跑一次全量检测，报告 SYNC-OK/DRIFT 入留痕；DRIFT 即按 §3 处理或挂起待机主裁定。
- 静态产物不设高频 cron。

## §5 诚实声明

- 检测器只报真实运行结果；词表缺失、路径不可读、版本号取不到一律显式标注（UNREADABLE 等），不以「大概是最新的」蒙混。
- 版本三段制；台账与实物不一致时以实物为准修台账，并留痕说明。
