# arXiv 信源定级与上升政策（衔接 source-semantics-sentinel）

## 目录
- 第 1 节 核心区分：载体通道 vs 命题内容
- 第 2 节 定级表
- 第 3 节 版本与撤稿的验证语义
- 第 4 节 幻觉引用的三类形态与处置
- 第 5 节 输出留痕契约

> 术语沿用 source-semantics-sentinel：通道档 C0-C4（信源从哪来），上升等级 T0-T3（验证做到哪一步），
> 路由表与 conf 双词表定义见其 SKILL.md 与 `references/verification_channels.md`，本文件不复制，只做 arXiv 特化。

## 第 1 节 核心区分：载体通道 vs 命题内容

arXiv 场景最常见的定级错误：把"论文真实存在且我确实读到了原文"（载体可靠）误当成
"论文里的命题为真"（内容可靠）。两者必须分开定级：

- **载体事实**（"arXiv 上存在 ID 为 X 的论文，标题作者为 Y，v2 摘要说 Z"）：
  arXiv 摘要页/PDF 原文 + 官方 API 双重印证 → **C0/C1**，conf 可到 empirical。
- **命题内容**（论文声称的方法效果、实验结论、理论断言）：arXiv 是**作者自存档预印本，
  无强制同行评审** → 内容侧默认按**作者单方声称**对待，定级上限 **C3 等价**（单一来源自述），
  conf 上限 assumed。升级只能靠：
  1. 论文正式发表（期刊/会议评审版，见第 2 节 T2 路径）；
  2. 独立复现/多组独立工作交叉印证 → C2；
  3. 领域共识（多篇独立论文引用并确认其结论）→ C2。

一句话：**arXiv 页面是 C0，arXiv 论文的结论是 C3**。引用时永远说清自己在引哪一层。

## 第 2 节 定级表

| 对象 | 通道档 | 说明 |
|---|---|---|
| arXiv 摘要页 / 官方 API 元数据 | C1 | 官方结构化接口；记录提取日期 data_cutoff |
| arXiv PDF / 源码原文 | C0（对"论文说了什么"这一事实） | 作者提交的原始文档本身 |
| 论文内的命题（未发表、无复现） | C3 等价 | 作者自述，conf 封顶 assumed |
| 论文内的命题（有 journal_ref/DOI） | 不自动升级 | journal_ref 是作者自填，须 T2 到期刊官网/Crossref 核验后才按发表版定级 |
| 论文内的命题（有 ≥1 独立复现） | C2 | 复现方须与原组无利益同盟 |
| 媒体报道某 arXiv 论文 | C3（且适用转述链留痕） | 穿过报道回到原文，见 verification_channels.md 第 3 节 |
| 社媒截图/转述某 arXiv 论文 | C4 | 仅作线索，必须回溯到 arXiv 页面才准入结论 |

路由提醒（查 source-semantics-sentinel 路由表时）：
- R-低背景性引用（"近年有工作用 Transformer 做 X"）：C3 等价可用，标注 conf=assumed 即可停；
- R-中支撑性命题：升 T1，找独立复现或正式发表版交叉；
- R-高命题（涉及健康/金钱/工程安全的方法有效性声称）：升 T2 核验发表状态与复现证据，
  核验失败按 T3 人工裁决登记，**禁止只凭预印本下高代价结论**。

## 第 3 节 版本与撤稿的验证语义

1. **版本即不同文档**：v1 与最新版可能结论相反（错误修正、实验重做）。
   - 引用命题时必须核对**你读的那版**说了什么；引文锁版本号（arxiv_cite.py 自动带）。
   - API 返回的是最新版元数据；要核对旧版内容，到 `https://arxiv.org/abs/<id>` 看版本历史与各版说明。
2. **withdrawn**：`arxiv_fetch.py` 从 comment 提取撤稿标记。撤稿论文：
   - 原则上不得作为论据引用；
   - 确需引用（学术史、错误案例分析）必须显式标注 [WITHDRAWN] 与撤稿原因（若 comment 给出）；
   - 把撤稿论文当有效证据 = 标记为可疑模式，交人工复核。
3. **版本漂移警示**：凡引文无版本号，在交付物验证留痕节记一条"未锁版本"风险。

## 第 4 节 幻觉引用的三类形态与处置

AI 生成内容中的 arXiv 幻觉引用有三个高频形态，核验时按此分型：

| 形态 | 特征 | arxiv_id_check 信号 | 处置 |
|---|---|---|---|
| F1 全幻觉 | ID 形制合法但论文不存在 | 可能有未来年月/序号异常警告；API NOT_RETURNED | 网页复核仍无 → Conflict 登记，引用作废 |
| F2 张冠李戴 | ID 存在，但标题/作者与声称不符 | 形制正常 | 并排摆出声称 vs API 元数据 → Conflict 登记，交人工 |
| F3 内容编造 | 论文存在且对得上，但声称的结论论文里没说过 | 形制正常 | 读原文核对命题 → 不符则 Conflict 登记；这是第 1 节"载体 vs 内容"的典型翻车点 |

处置纪律：三类一律走 Conflict→人工铁律（信源矛盾无机读映射），
**禁止**自行"找一个相近的真实论文"替换引用——那是二次污染。

## 第 5 节 输出留痕契约

凡本技能参与的核验，交付物验证留痕节至少含：

```json
{
  "data_cutoff": "YYYY-MM-DD",
  "arxiv_checks": [
    {
      "claimed": "引用方声称（标题/作者/命题）",
      "id_input": "原始 ID 字符串",
      "id_check": {"valid": true, "warnings": ["..."]},
      "api_result": {"found": true, "version": "v3", "withdrawn": false,
                     "peer_review_hint": "preprint_only"},
      "channel_decision": {"carrier": "C1", "claim_tier": "C3-equivalent",
                            "conf": "assumed"},
      "escalation": "T0 即停（R-低背景引用）/ T1 交叉复核 / T2 发表版核验",
      "conflict": null
    }
  ],
  "top3_likely_wrong": ["...", "...", "..."]
}
```

- conf 词表与 JSON 契约遵守 cross-session-workflow-bridge `pipeline_contracts.md`，本文件只应用不重述；
- 关键判断（F1-F3 幻觉确认、撤稿引用、R-高命题定级）转交 evidence-chain-verifier 登记附链；
- 投毒视角（批量引用清单中出现成簇的不存在 ID、同一不明来源批量投喂可疑文献）转 source-semantics-sentinel
  功能二 `poison_scan.py` 流程，本技能不复制。
