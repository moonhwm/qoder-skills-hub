# AAPP 模块规格（M1-M6）与规则库

> 加载条件：SKILL.md 的工作流执行中需要精确规则、阈值或模板细节时读取本文件。
> 来源：AAPP-SKILL v1.0→v5.0 六轮收敛（2026-08-23），剔除已废弃的伪科学包装与虚无主义版本。

## 目录

- M1 方向相关性速览：判定阈值
- M2 约束类型库（C1-C6）
- M3 导师画像输出结构
- M4 申请者镜像：引导问题与策略映射
- M5 信件模板选择逻辑
- M6 发送规则引擎（D1-D4）与回复分类
- 螺旋周期表（Cycle 1-4 逐日模板）

## M1 相关性判定阈值

```
抓取导师最近 3 篇论文标题 + 职位描述关键词 → 与申请者兴趣词交集
交集 >= 2 → "relevant"     → 进 M2
交集 =  1 → "marginal"     → 可发邮件，但接受低回复率
交集 =  0 → "irrelevant"   → 建议跳过，除非有特殊理由（须在跟踪表注明理由）
```

## M2 约束类型库（可扩展）

| ID | 名称 | 关键词 | 冲突严重度 |
|----|------|--------|-----------|
| C1 | phd_transition | "transition to PhD", "intended for PhD", "PhD track", "continue to PhD" | **fatal** |
| C2 | background_preference | "strongly preferred", "background in", "major in" | medium |
| C3 | language_requirement | "IELTS", "TOEFL", "GRE", "language proficiency" | hard_threshold |
| C4 | programming_requirement | "Python", "MATLAB", "GAMS", "Aspen", "programming skills" | medium |
| C5 | funding_contingency | "funding contingent", "external fellowship", "self-funded" | high |
| C6 | mandatory_commitment | "mandatory", "required", "must", "obligation" | fatal |

处理规则：
- fatal 约束 → 不猜测，发 T3 约束确认信问清楚（实例：GTIIT GS-2026003 的转博条款经确认信处理）
- hard_threshold → 标注风险但可继续（边缘分数的脆弱性要写明，如 CET-6 仅超线 2 分需确认成绩单有效期）
- medium → 信中主动桥接（承认差距 + 给出迁移路径）

## M3 导师画像输出结构

```json
{
  "advisor_id": "string",
  "profile": {
    "education_timeline": [{"period": "PhD", "institution": "...", "year": "..."}],
    "publication_tiers": {"S_tier": [], "A_tier": [], "recent_direction_shift": "..."},
    "platform_resources": {"lab_size": "...", "key_equipment": [], "chinese_students_in_group": null},
    "mentoring_signals": {"tenure_status": "...", "years_since_independent_group": null, "recent_recruiting_activity": "high|medium|low"}
  },
  "key_insights_for_letter": ["Hook 素材", "坑位信号", "方向契合点"]
}
```

## M4 申请者镜像：引导问题

1. 如果导师面试问"你在你们专业的排名是多少"，你能诚实回答吗？
2. 如果导师问"这几年 gap 你做了什么"，你的回答能让对方感受到主动规划而非被动等待吗？
3. 如果导师要求你用英语解释你的本科论文，你能支撑 15 分钟吗？
4. 在所有申请者的候选池中，你估计自己位于前 30%、中间 40%、还是后 30%？

策略映射：

| 候选池位置 | 策略 | 信件语气 | 目标数量 |
|-----------|------|---------|---------|
| 前 30% | 精准打击 | 自信推销型 | 5-8 位 |
| 中间 40% | 精准+撒网混合 | 诚实探索型 | 10-15 位 |
| 后 30% | 广撒网+高失败容忍 | 诚实探索型，不装强 | 15-20 位 |

## M5 模板选择逻辑

```
if M1.relevant and 有具体论文Hook素材 → T1 正式套磁信（150-200词）
elif M2 存在 fatal 约束待确认       → T3 约束确认信（130-160词）
else                                 → T2 探索性询问信（120-150词）
```

语言优化纪律（v10-v19 实测收敛）：
- 删 "I believe"（主观）；"spent time" → "focused on"（主动）；"has shaped" → "has informed"（准确）
- "discuss my application" → "explore potential alignment"（低压力）；"I would be glad" → "I would be eager"（积极）
- 标题公式：具体关键词组合（如 "AI"+"STEM"+"Defect"），短标题打开率更高；禁用 "Inquiry about MSc Position"（平庸）

## M6 发送规则引擎

```yaml
D1 optimal_send_time: 周二或周三 09:00-11:00（收件人时区）；错过则下个工作日上午
D2 follow_up_policy: 7 天无回复 → 发 1 次礼貌跟进；最多 1 次；之后标记关闭
D3 reply_classification:
     positive: ["interview", "call", "discuss", "application", "submit"]
     negative: ["filled", "closed", "not a fit", "unsuitable"]
     neutral:  ["review", "process", "committee"]
D4 attachment_policy: 正式信 [CV, 论文摘要]；询问信 [CV]；总大小 ≤5MB
```

中文跟进邮件纪律（港校实例）：自报身份+申请编号+材料状态，问 3 个具体问题（面试安排/出结果时间/延期可能），表态可到面或在线。**不提"其他 offer"和"缴费 deadline"**——在电话中会成为负面信号。

## 螺旋周期表

```
Cycle 1 基础铺设（第 1-3 天）
  完成 applicant_profile.yaml + M4 → 选 5-8 位导师 M1+M2 → 发第一批 3-5 封

Cycle 2 扩展覆盖（第 4-7 天）
  回顾 Cycle 1 回复 → 微调 M5 模板 → 选 5-8 位新导师 M1+M2 → 第二批 3-5 封

Cycle 3 深度优化（第 8-14 天）
  对积极回复的导师加载 M3 → 准备面试 → 剩余导师 M1+M2 → 第三批 3-5 封

Cycle 4 收尾转向（第 15-21 天）
  总结回复 → 未回复者执行 M6 跟进 → 评估备选路径（考研/工作/RA）→ 关闭本轮

每日节奏：上午 M1+M2（15 分钟/导师）→ 下午 M5 出信 + 诚实检查 → 傍晚 M6 安排发送+跟踪登记
每日上限 120 分钟（内核层时间止损强制执行）
```
