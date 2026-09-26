# 机械证明算法谱系(atp_algorithms.md)

> 用途:为形式化后的数学分析命题选证明算法。口径:综述性转述,具体定理有效性声称按作者单方声称对待。

## §1 历史谱系(骨架)

1956 Logic Theorist(Newell-Simon)→ 1960 王浩命题逻辑程序 → 1963 戴维斯-普特南(DP)→ 1965 Robinson 归结原理(resolution,一阶完备的反驳演算)→ 1970s 表格法(tableau)与模型消除 → 1980s Knuth-Bendix 完成(等式重写)→ 1990s 叠加演算(superposition,等式一阶)→ 2000s SMT(可满足性模理论,DPLL+理论求解器)→ 2010s hammer 时代(Isabelle Sledgehammer 调 E/Vampire/SPASS/z3)→ 2020s 神经前提选择+LeanDojo/LLM 证明搜索。

## §2 算法卡

| 算法 | 片段 | 完备性 | 何时用 |
|---|---|---|---|
| 归结 resolution | 一阶子句 | 反驳完备 | 通用一阶 |
| 表格 tableau | 一阶自由变量 | 完备 | 结构化证明 |
| 叠加 superposition | 等式一阶 | 反驳完备 | 含等式 |
| SMT(DPLL+T) | 线性算术/数组/位向量等可判片段 | 片段内可判定 | 不等式链、线性 |
| 决策程序 ring/linarith | 交换环恒等式/线性算术 | 可判定 | Lean 中代数收尾 |
| 区间算术/泰勒模型 | 实函数不等式 | 半判定 | 实数估计 |
| premise selection | 大库检索 | 启发 | 从 Mathlib 找引理 |
| hammer | 组合调用外部 ATP/SMT | 继承各件 | 交互式主力 |
| LLM 证明搜索(LeanDojo 类) | 策略生成 | 启发 | 补洞与草稿 |

## §3 ε-δ 命题的算法选择决策树

1. 代数恒等式变形为主 → Lean `ring`/`field_simp`/`linarith` 决策程序;
2. δ 显式构造(模板 §6 三卡)→ 取 δ→代入→代数收尾(决策程序);
3. 需存在性引理(确界/柯西)→ 查 Mathlib 引理库(premise selection),不要重证完备性;
4. 一致连续 → 优先 Lipschitz 捷径(f' 有界),落 `LipschitzWith.uniformContinuous`;
5. 反例嫌疑 → 先数值侦察(delta_search.py),坐实即转否定式证明;
6. 大库综合 → hammer + 人工补洞;LLM 草稿须证明器验收才入账。

## §4 硬边界(诚实声明)

- 实数完备性(确界原理、柯西判据)不可在纯一阶片段内机械判定;实践走 Mathlib 已证引理或区间方法;
- ∀ε∃δ 是 Π₂ 语句:可半证伪(反例搜索)不可一般判定;δ 的显式构造成功率依赖函数类;
- 神经证明搜索的产物必须过证明器内核——"模型说证了"不算证(与主权 §5 假证明禁令同)。

## §5 工具落地速查

- Lean4+Mathlib:`import Mathlib`,极限 `Metric.tendsto_nhds_nhds`,连续 `Continuous`,一致连续 `UniformContinuousOn`;
- Coq:`Coquelicot` 实分析库;Isabelle/HOL:`HOL-Analysis`;Metamath:set.mm 实分析段;
- 外部 ATP:E/Vampire;SMT:z3/cvc5;桥:Lean hammer 生态(lean-auto 等)。
