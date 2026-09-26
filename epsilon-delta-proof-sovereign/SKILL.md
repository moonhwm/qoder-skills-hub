---
name: epsilon-delta-proof-sovereign
description: >
  ε-δ 机械证明主权——把数学分析的形式化语言（ε-δ 极限/连续/一致连续/导数/积分语句族）
  当作机械证明的输入语法，探讨并落地"数学分析命题 → 形式化 → 自动/交互定理证明"的
  完整算法谱系（判定程序、归结、表格法、SMT、叠加、Lean4/Mathlib hammer、premise
  selection、证明搜索），并作为主权的总括件：联挂自决(自决)、赤子续行(goal-child-ops)、
  伞(hifi-integration-umbrella)、穷举总署(omni-exhaust-research-ops)、强制裁判执法局、
  语义肿瘤科、技能刷新、输出裁决门，把 verifier 制度视为"判定程序"、runs 轨迹视为
  "证明轨迹"同构治理。触发(满足任一)：①用户要求把极限/连续/导数等数学分析命题
  形式化为 ε-δ 或等价形式语句；②要求做数学机械证明/自动定理证明(ATP/ITP、Lean、
  Coq、Isabelle、Metamath、SMT)或证明搜索；③要求探讨形式化语言在证明算法上的
  可判定性/复杂度边界；④要求对以上八大主权件或本对话研究做总括/修典；⑤出现
  "ε-δ""机械证明""形式化数学""证明助手""epsilon delta"等关键词。不覆盖：具体数学
  猜想的内容级证明（那是数学工作本身，本件给方法管线）、对命题真值的超出形式系统
  的哲学断言。English triggers: epsilon-delta formalization, automated theorem proving,
  proof search, Lean4 formalization, mechanical proof sovereignty.
---

<!-- v1.1（2026-09-03，评估侧采纳 2026-09-02 压测修订建议三条）：references 增 pressure_test_20260902.md 压测档案；模板库 §7 增第 6 条判具记号宽容注记；§4 增主权记忆评估 RAG 注记。技能本体经压测裁定无需返修。 -->

# ε-δ 机械证明主权(epsilon-delta-proof-sovereign)

> 立法锚两句：
> **「ε-δ 不是记号，是机器可判的语法——凡能写成 ∀ε>0 ∃δ>0 的命题，都在算法的射程之内。」**
> **「verifier 即判定程序，runs 即证明轨迹——主权的治理术与机械证明同构。」**

## §0 定位与边界

- 本件把数学分析形式化语言(ε-δ 族)与机械证明算法谱系焊接：给"命题形式化→证明自动化"一条标准管线，并把本对话燃烧战史与八大主权件总括为一部可检索的治典。
- 诚实边界：ε-δ 数值搜索(scripts/delta_search.py)是**计算启发**而非证明——它给出候选 δ 与反例筛除，形式证明仍须走 §2 管线的证明器；预印本/工程口径证据按各自信源等级引用；主权语义一律沙盘类比。
- 安装位只读漂移：本件以 .skill 包交割(若 <技能安装位> 可写则安装，只读则维持漂移标注并在每次触发时重申)。

## §1 触发即办(三路由)

| 用户来意 | 去处 |
|---|---|
| 把这个命题写成 ε-δ/形式语句 | references/epsilon_delta_formalization.md 查模板 → 给出语句+否定式+邻域图 |
| 给我证明/机械证明/Lean 化 | §2 五步管线 → references/atp_algorithms.md 选算法 |
| 总括八件/修典/本对话战史 | references/sovereign_synthesis.md |

## §2 命题→证明 五步管线

1. **解析**:把自然语言命题映射到 ε-δ 模板(极限/连续/一致连续/导数/积分五族，见 references/epsilon_delta_formalization.md §1-§5)，同时写出**否定式**(机械证明常从否定式出发做归谬)。
2. **数值侦察**:跑 `python3 scripts/delta_search.py --f <表达式> --c <点> --L <极限> --eps <值>`(仅 numpy)，得候选 δ 与疑似反例；侦察失败=命题可能为假或模板选错，如实报告，**不硬证假命题**。
3. **形式化**:选目标系统——Lean4/Mathlib(首选,社区与 hammer 最强)/Coq/Isabelle-HOL/Metamath；把模板落成该系统的定理语句。
4. **证明搜索**:按 references/atp_algorithms.md §3 决策树选术——代数恒等式→ring/linarith 决策程序；一阶→归结/叠加;SMT 可判片段→z3 风格;库检索→premise selection;综合→hammer(sledgehammer 类)+人工补洞。
5. **验证留痕**:证明器通过才算证；把命题/模板/算法选择/证明脚本/结果存入 runs 式轨迹(与主权 verifier 同构,§4)。

## §3 ε-δ 语句族的算法性质速查

- ∀ε∃δ 形为 Π₂ 语句：**不可判定但可半证伪**(数值反例搜索)——delta_search 利用的正是这点；
- 多项式/有理函数极限：ε-δ 可机械化消元(δ 取 ε 的多项式函数),templates §6 给了三类机选 δ 公式;
- 一致连续：δ 只依赖 ε 不依赖点——机械化关键在消去点参数;
- 实数完备性(确界/柯西)是机械证明的硬边界：需要非阿基米德或区间方法,见 references/atp_algorithms.md §4。

## §4 主权总括(治典)

本对话与八大主权件的总括全文在 references/sovereign_synthesis.md，要点：
- **同构**:verifier v1-v27=判定程序族；runs/=证明轨迹;verdict gate=证后裁决门；
- **战史**:双炉 2,345万+ tokens、31 组件、1,065 章、原型机 10 件、行研+arXiv 两书；
- **八件联挂边界**:见 references/sovereign_synthesis.md §3 表(缺席即声明能力占位,禁止假装可调度)。
- **主权记忆评估须 RAG**(2026-09-02 压测实证):考核主权总括内容时技能原文须在被测上下文在场,缺席时「声明无法访问再作答」是合规表现而非缺陷;判具须宽容 LaTeX 记号变体。压测档案:references/pressure_test_20260902.md。

## §5 红线

凭据铁律;假证明禁令(delta_search 输出≠证明,措辞必须区分"数值侦察"与"已证");R-高命题(金钱/健康/安全相关定理有效性声称)升 T2 核验,失败按 T3 人工裁决;冲突时按 hifi-integration-umbrella §2 仲裁序从严。
