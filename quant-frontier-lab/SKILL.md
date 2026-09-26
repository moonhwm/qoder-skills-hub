---
name: quant-frontier-lab
description: 前沿算法实验台——教学级量化算法工具箱，覆盖 Gale-Shapley 志愿填报匹配、PSM 倾向得分/因果推断、DID 前置评估、SIR 传染模型（Gillespie/链二项式/边基分区）、谱半径免疫、MAML/Reptile 元学习玩具演示、Time-MoE/时间序列预测选型门槛咨询、纳什均衡与算法选型。诚实性优先：一切"预训练/大模型"表述配 L0-L3 严肃等级与局限声明，禁止伪造训练结果。中文名：前沿算法实验台
---

# Quant Frontier Lab · 前沿算法实验台

<!-- v1.0.1（2026-08-24）
这是中文解释：v11 质检修复——补五件套立场节、Lemke-Howson 门槛判定前后统一、互指双向化 -->

## 定位

教学级（L0/L1）量化算法实验台：每个脚本可实跑、带自检、附诚实等级标注。
**本技能不产出任何"预训练模型"，不做超出数据规模的方法承诺。**

## 三条铁律

1. **诚实等级标注**：所有输出必须携带严肃等级（L0 玩具 / L1 原型 / L2 生产前验证 /
   L3 生产级，对齐 iteration-convergence-ops 严肃化阶梯）与局限声明。
   任何"预训练/大模型/SOTA"类表述必须降级为实际等级或拒绝；禁止伪造训练结果、
   禁止挑选随机种子美化指标。
2. **归档纪律**：一切训练产出（参数、损失曲线、配置、诚实标注）自动写
   `<输出区>/models/YYYY-MM-DD/`（脚本自建目录），stdout 报告实际路径；
   不得在对话中谎称已归档而未写盘。
3. **方法选择先看门槛表**：任何"要不要上 X 方法"的判断，先查
   `references/method_selection.md` 的门槛表并给出"达到/未达到"的诚实判定
   （当前项目对深度时序、真实元学习、NOTEARS、CFR/GNE 等大多数为**未达到**）。

## 五件套立场

- **data_cutoff**：脚本为确定性算法，本身无外部数据时效；凡输出引用了外部事实
  （如 meme_calibrator 的采样记录），必须逐条带采样日期，默认 data_cutoff=当天。
- **top3_likely_wrong**：每次正式使用（非 smoke）在输出末尾给出最可能错的 3 个点
  （如 PSM 的未观测混淆、谱免疫的贪心次优、匹配的假想偏好）。
- **选择题式交付**：算法选型类问题给 2-4 个候选方法+推荐项+理由（门槛表即素材）。
- **conf 三级**：输入数据的 conf 逐字段标注（empirical/estimated/assumed 管道层
  词表对齐 pipeline_contracts）；脚本输出本身标 L 等级。
- **收割指针**：会话结束按 cross-session-workflow-bridge 的 session_harvest 规程
  产出追问与排期；训练归档目录即收割素材之一。

## 路由表（用户信号 → 脚本/参考）

| 用户信号 | 路由 | 说明 |
|---|---|---|
| Gale-Shapley、志愿填报匹配、稳定匹配、院校-考生双边 | `scripts/gale_shapley.py` | stdin JSON `{students, schools}`；容量可配；阻塞对自检断言为 0 |
| PSM、倾向得分、院校公平对比、混淆平衡、SMD | `scripts/psm_balance.py` | 手写 IRLS logistic（无 sklearn）；卡钳 0.2×SD(logit)；含混淆清单人工确认硬提示 |
| 因果推断、DID、ATT、AIPW、因果森林、NOTEARS、PC、LiNGAM | `references/method_selection.md` §4 | 先门槛判定；当前仅 PSM 达门槛，其余多为未达到 |
| SIR、传染模型、Gillespie、链二项式、边基分区、再生数 | `scripts/sir_advanced.py` | 三算法对比；附均匀混合假设警示 |
| 谱半径免疫、网络免疫、传播阈值、边基分区免疫 | `scripts/spectral_immunity.py` | 幂迭代 λ₁ + 贪心免疫；小规模可 `--exact-check` 穷举对照暴露贪心差距 |
| meme_strength、热度校准、学校热度、公开信号 | `scripts/meme_calibrator.py` | 仅用合规公开信号（web_search 计数/人工录入公开指数）；输出 conf=估算 + 采样记录表；脚本不爬登录墙 |
| 元学习、MAML、Reptile、少样本适应、原型网络 | `scripts/meta_toy.py`（L0 玩具）→ `references/method_selection.md` §3 | 玩具正弦回归；训练产物自动归档 `<输出区>/models/日期/` |
| Time-MoE、PatchTST、iTransformer、Autoformer、TCN、N-BEATS、Prophet、时间序列预测 | `references/method_selection.md` §1–2 | 当前数据（数十至数百行、年度单点序列）全部未达到深度时序门槛；首选移动平均/线性趋势 |
| 纳什均衡、Lemke-Howson、CFR、GNE、LegoNE、博弈 | `references/method_selection.md` §5 | 志愿问题现实抽象是匹配而非均衡求解；NE 类当前均未达门槛 |
| 算法选型、方法门槛、数据规模够不够、要不要上深度模型 | `references/method_selection.md` §6 速查表 | 给"达到/未达到 + 一句话理由" |
| 局限性、严肃等级、升级路径、能信吗 | `references/limitations.md` | 每脚本局限清单 + L1→L2/L3 升级触发条件 |

## 脚本用法速览

所有脚本：`--smoke` 实跑冒烟；否则从 stdin 读 JSON、向 stdout 写 JSON。

```bash
# 稳定匹配（4 考生×3 校冒烟）
python3 scripts/gale_shapley.py --smoke
echo '{"students":[...],"schools":[...]}' | python3 scripts/gale_shapley.py

# PSM 平衡（30 校合成冒烟）
python3 scripts/psm_balance.py --smoke

# SIR 三算法对比（N=500 冒烟）
python3 scripts/sir_advanced.py --smoke

# 谱免疫（20 节点、含穷举对照冒烟）
python3 scripts/spectral_immunity.py --smoke

# 热度校准（合规信号冒烟）
python3 scripts/meme_calibrator.py --smoke

# 玩具元学习（归档到 <输出区>/models/日期/）
python3 scripts/meta_toy.py --smoke
```

## 依赖与降级

- 仅标准库 + numpy（可选）。numpy 缺失时 `psm_balance.py` 降级纯 Python 梯度下降
  （输出 `backend` 字段标注降级）；其余脚本本就纯标准库。
- 沙箱只做轻量可运行实现：无 GPU、无外部权重、无网络抓取。

## 参考文档

- `references/method_selection.md` — 方法选择路径原因与门槛表（重点诚实文档，
  含每类方法"当前项目是否达到引入门槛"判定）。
- `references/limitations.md` — 每脚本教学级局限、L1 原型定位声明、升级路径。

**互指**：扩散/传播类问题的模型假设审查与严肃等级裁定走
`diffusion-dynamics-extension`（演化推演器，安装后位于 <技能安装位>/；
未安装时本指针忽略）；本技能负责其高阶算法实现与参数归档。
