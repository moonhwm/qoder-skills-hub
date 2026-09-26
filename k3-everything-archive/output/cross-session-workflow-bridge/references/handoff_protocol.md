# 交接协议（long-session-handoff）——交接五件套 + SKILL 生成规格（可选第六件）

> v2.0（2026-08-28 落地，修改人：skill-evaluation/Orchestrator；草案成文于 2026-08-27 会话，因 <技能安装位> 运行期只读未能装上，本轮补装）
> 新增：交接文档尾部可选追加 SKILL 生成块（skill_gen YAML），使交接包可被 集群甲自动汇总为 `.skill` 包。

适用时机：长会话将尽、用户说「交接」「给下个会话」、或模式切换（如 Kimi 2.6 快速模式 ↔ K3 长对话集群）。真实案例：CSCI 城市舒适度项目用本模式完成向 集群甲的交接。

五件套**全部**落盘到 `<上传区>/handoff_<项目名>_<日期>/`（或项目既有目录），完成后 `ls` 核验并输出清单。任何一件缺失都不得宣布「交接完成」。第六件（SKILL 生成块）为可选——仅当本次会话沉淀出可复用工作流时追加。

## 一、交接文档（handoff_doc.md）模板

```markdown
# 交接文档：<项目名> <日期>
## 现状
- 已完成：（逐条列，附文件路径与版本号）
- 进行中：（线程名 + 卡在哪一步）
## 硬结论（【必读】，后续产出不得矛盾）
1. <结论>（来源：<文件快捷码/路径>）
## 未决项（按优先级排序）
| # | 未决问题 | 阻塞原因 | 建议下一步 | 需用户线下动作? |
|---|----------|----------|------------|------------------|
| 1 |          |          |            | 是/否            |
## 风险提示
- 哪些结论置信度低、哪些数据即将过期（写清 data_cutoff）
```

**可选——若本次会话沉淀出可复用工作流，在文档尾部追加 SKILL 生成块**（集群甲可自动解析并生成 `.skill` 包）：

```yaml
---
skill_gen
name:               # kebab-case 技术名，如 solar-pv-due-diligence
display_name:       # 中文名，2-6 字，如 光伏尽调助手
description:        # 触发描述：什么场景、解决什么问题、何时使用。尾部固定格式：中文名：XX
version:            # v1.0
derived_from:       # 本会话项目名
aliases:            # [别名1, 别名2]
workflow_summary:   # 一句话概括本技能解决什么问题
reusable_components:# 本次会话中可复用的脚本/引用/资产
  - type: script
    path:           # 相对于交接目录，如 scripts/extract_financials.py
    purpose:        # 一句话用途
  - type: reference
    path:           # 如 references/industry_schema.md
    purpose:        # 用途
  - type: asset
    path:           # 如 assets/template.xlsx
    purpose:        # 用途
pipeline_links:     # 与上下游技能的管线对接
  - producer:       # 上游技能名或 null
    consumer:       # 下游技能名或 null
    data_format:    # JSON schema 名或 null
confidence:         # empirical | estimated | assumed
data_cutoff:        # YYYY-MM-DD
---
```

写作规则：硬结论逐条引用快捷码（如 [FO-V1][CE-V23]），不凭记忆复述数字；未决项必须给出「下一步」，不允许只写「待研究」。

## 二、可信数据集

- 把交接所依赖的数据文件**原样拷贝**进交接目录（不要只写路径引用 output 下的文件——output 不保证跨会话）。
- 配一份 `DATA_README.md`：每个文件的口径、来源、data_cutoff、已知缺陷。

## 三、可运行引擎/脚本

- 拷贝脚本本体 + 一行可复制的运行命令；交付前**实测跑一次**确认退出码 0。
- 若依赖第三方包，写明 `pip install` 清单；优先纯标准库实现。

## 四、状态看板 JSON（status_board.json）schema

```json
{
  "project": "项目名",
  "updated_at": "YYYY-MM-DD",
  "handoff_from": "本会话模式/标识",
  "handoff_to": "目标会话模式（如 K3 长对话集群）",
  "threads": [
    {
      "id": "THREAD-01",
      "name": "线程名",
      "status": "pending | in_progress | blocked | done",
      "latest_version": "vX.Y",
      "next_action": "下会话可立即执行的一步（具体到文件/命令）",
      "key_files": ["<上传区>/..."],
      "conf": 0.0,
      "data_cutoff": "YYYY-MM-DD",
      "top3_likely_wrong": ["最可能错的三处"]
    }
  ],
  "first_task_next_session": "下会话首任务（一句话）"
}
```

校验规则：`threads` 至少一项；每个 thread 必含 `next_action` 与 `key_files`；`conf`/`data_cutoff`/`top3_likely_wrong` 三字段必填（与管线数据契约一致，见 pipeline_contracts.md）。

## 五、下会话首任务卡（first_task_card.md）模板

```markdown
# 下会话首任务卡：<项目名>
- 首任务：<一句话，可在新会话内完成>
- 前置阅读：<索引路径> → <【必读】文件列表>
- 执行入口：<脚本命令 或 要编辑的文件路径>
- 验收标准：<可检查的完成条件>
- 预计耗时：<粗估>
```

## 交接收尾 checklist

1. 五件套全部写入 upload 并 `ls` 核验存在；若追加了第六件（SKILL 生成块），确认其 YAML 可解析、name 为 kebab-case 且与 `references/skill_naming_paradigm.md` 的中文命名范式一致；
2. MASTER_INDEX 回写本次交接目录的快捷码与路径；
3. 状态看板 JSON 通过 schema 校验规则自检；
4. 向用户输出交接清单（文件路径 + 一句话摘要）。
