# 正交性判定方法与实测底稿（tongtu-hub v4 熔铸的客观依据）

> 立法（用户，2026-09-29）：正交性判定必须严格依据阿里云百炼、华为云 MaaS、腾讯云 TokenHub
> 及火山引擎等向量模型的输出结果并结合相似度计算执行；严禁主观经验、直觉判断或未经核实的
> 粗略比对。本文件是该立法的执行底稿——判定规则先于测量声明，全部数值可复跑。

## 一、会裁面板（四路，两在轨两降级，如实声明）

| 通道 | 端点 | 模型 | 维度 | 状态 |
|---|---|---|---|---|
| 阿里云百炼 | dashscope.aliyuncs.com/compatible-mode/v1/embeddings | text-embedding-v3 | 1024 | **在轨**（gift 键；主键 401 登记） |
| 腾讯云 TokenHub | tokenhub.tencentmaas.com/v1/embeddings | kinfra-text-embedding-4b | 2560 | **在轨**（/models 实测选型） |
| 华为云 MaaS | api.modelarts-maas.com/v1/embeddings | bge-m3（西南-贵阳一） | —— | **降级**：凭据占位未实装（盘古执法局：候选已纳入、缺席原因登记） |
| 火山引擎 | ark.cn-beijing.volces.com/api/v3/embeddings | doubao-embedding-text-240515 | —— | **降级**：API Key 401 / AKSK 403，需控制台重签 |

降级纪律：会裁不足四路即如实标注「不足即降级」，单通道结论永不冒充双通道 IN（orthocheck.py judge 单通道上限=EDGE）。

## 二、判定规则（先声明后执行）

- **IN（非正交，须融合）**：内容级双通道排名均 top5，且双通道 z 均值 ≥ 1.0；
- **边界（引用不合并）**：单通道 top5，或 z 均值 ∈ [0.7, 1.0)；
- **OUT（正交）**：其余。
- z 以全库两两余弦背景分布为参照：z=(sim−μ)/σ。

## 三、背景分布与面板一致性（119 件技能全库实测，2026-09-29）

| 通道 | μ | σ | p95 | p99 |
|---|---|---|---|---|
| 百炼 text-embedding-v3 | 0.5559 | 0.0628 | 0.6508 | 0.6952 |
| TokenHub kinfra-4b | 0.4341 | 0.0832 | 0.5668 | 0.6369 |

双通道两两矩阵 Spearman ρ=0.6737（p=6.26e-17，N=118）——两通道排序显著一致，
会裁有效（若 ρ 不显著，本方法整体降级为单通道声明制）。

## 四、对 tongtu-hub 的判定结果（三级证据）

| 证据级 | 通道 | top 命中 |
|---|---|---|
| 内容级（主） | 百炼 / TokenHub | ① k3-channel-ops 0.6397/0.6499（z 1.33/2.59）② cross-session-workflow-bridge 0.6427/0.5672（z 1.38/1.60）③ ultra-compress-ops 0.6335/0.4807 |
| desc 级（辅） | TokenHub（百炼额度烧尽降级） | k3-channel-ops 0.5416、cross-session-workflow-bridge 0.4772 |
| 段落级（辅） | TokenHub | k3-channel-ops 0.7017、cross-session 0.6019、skill-dispatch-hq 0.5720、star-chain-ops 0.5564、ultra-compress 0.5178 |

**终判**：
- **IN = {k3-channel-ops（z 均 1.96）、cross-session-workflow-bridge（z 均 1.49）}** → 熔铸合并（运维层/通道选型切片）；
- **边界 = {ultra-compress-ops、skill-dispatch-hq、star-chain-ops、openpangu-seat-ops、plugin-datasource-ops、vision-intake-ops}** → 引用不合并；
- 其余 111 件 OUT。

## 五、复跑方法

```bash
python3 scripts/orthocheck.py --desc "<候选描述>" --registry corpus.json \
    --providers bailian,tokenhub,huawei,volcengine --json report.json
python3 scripts/orthocheck.py --smoke   # 离线自检：12 项断言含 6 负断言
```

凭据仅经环境变量注入（见 orthocheck.py 头注释），零落盘；缺席通道自动降级登记。

## 六、已知边界（诚实声明）

1. 百炼免费额度于 2026-09-29 测量中烧尽（AllocationQuota.FreeTierOnly）——内容级主测量在烧尽前
   已 119/119 落盘，主判定双通道证据完整；desc/段落级由 TokenHub 单通道+Jaccard 机检补位，已登记。
2. 华为/火山两路未参与实测——四路会裁立法的目标态未完全达成，本版按「不足即降级」执行；
   两路凭据补齐后应复跑全库并将结果并入本文件 §四。
3. 向量相似度度量的是语义邻近，不是功能重叠的充分条件——IN 件经人工精读确认实质重叠后方合并，
   边界件保持引用关系，不做语义外推。
