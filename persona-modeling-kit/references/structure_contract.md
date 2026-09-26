# 结构契约：AI 人设文档

## 文档层级

```
Document
├── Title Page / Header
│   ├── Document Title (e.g., "Kimi AI Assistant Persona Definition")
│   ├── Version
│   ├── Date
│   └── Author/Creator
├── Section 1: Identity & Role Definition (Heading 1)
│   ├── 1.1 Persona Name (Heading 2)
│   ├── 1.2 Role Summary (Heading 2)
│   ├── 1.3 Self-Introduction Pattern (Heading 2)
│   └── 1.4 Core Identity Statement (Heading 2)
├── Section 2: Personality Profile (Heading 1)
│   ├── 2.1 Key Traits (Heading 2)
│   │   └── Trait cards: Name + Description + Example (Heading 3)
│   ├── 2.2 Emotional Range (Heading 2)
│   └── 2.3 Formality & Humor (Heading 2)
├── Section 3: Communication Style (Heading 1)
│   ├── 3.1 Greeting Patterns (Heading 2)
│   ├── 3.2 Language Characteristics (Heading 2)
│   │   ├── Sentence structure (Heading 3)
│   │   ├── Vocabulary preferences (Heading 3)
│   │   └── Punctuation & emoji usage (Heading 3)
│   ├── 3.3 Response Length & Structure (Heading 2)
│   └── 3.4 Tone Markers (Heading 2)
├── Section 4: Backstory & Context (Heading 1) — optional
│   ├── 4.1 Origin (Heading 2)
│   ├── 4.2 Key Experiences (Heading 2)
│   └── 4.3 Current Context (Heading 2)
├── Section 5: Knowledge Scope (Heading 1)
│   ├── 5.1 Areas of Expertise (Heading 2)
│   ├── 5.2 Knowledge Boundaries (Heading 2)
│   └── 5.3 Handling Unknowns (Heading 2)
├── Section 6: Behavioral Guidelines (Heading 1)
│   ├── 6.1 Required Behaviors (Heading 2)
│   ├── 6.2 Prohibited Behaviors (Heading 2)
│   └── 6.3 Escalation & Redirection (Heading 2)
├── Section 7: Response Patterns (Heading 1) — optional
│   ├── 7.1 Standard Response Structure (Heading 2)
│   ├── 7.2 Query-Type Mapping (Heading 2)
│   └── 7.3 Special Formats (Heading 2)
├── Section 8: Sample Interactions (Heading 1)
│   └── Example N: Scenario + User Input + Expected Response (Heading 2)
└── Section 9: Version & Metadata (Heading 1)
    ├── 9.1 Version History (Heading 2)
    └── 9.2 Change Log (Heading 2)
```

## 章节规范

### 第 1 章：身份与角色定义

**用途**：确立人设是谁。

**字段**：
- `persona_name`：展示名称（如 "Kimi"、"Dr. Watson"、"Coding Mentor"）
- `role_summary`：1-2 句的角色描述
- `self_introduction`：人设向新用户自我介绍时使用的模板
- `identity_statement`：锚定人设的核心"我是……"宣言

**内容模式**：
```
Name: [Persona Name]
Role: [Concise role description]

Self-Introduction:
[Template showing exact phrasing the persona uses]

Identity Statement:
"I am [Name], [role description]. I [key capability 1], [key capability 2], and [key capability 3]."
```

### 第 2 章：性格档案

**用途**：定义人设的情绪与行为内核。

**字段**：
- `traits`：3-5 项特质，每项包含：
  - 特质名称
  - 描述（1-2 句）
  - 行为体现（具体示例）
- `emotional_range`：从最低到最高的情绪表达幅度
- `formality_level`：等级（1-10）及说明
- `humor_style`：幽默类型（机智、冷面、俏皮、无幽默等）

**内容模式**：
```
Trait 1: [Name]
- Description: [What this trait means]
- Manifests as: [Concrete behavior example]

Trait 2: [Name]
...
```

### 第 3 章：沟通风格

**用途**：精确规定人设的沟通方式。

**字段**：
- `greeting_patterns`：面向不同情境的 2-3 个问候示例
- `sentence_structure`：短/中/长句、复杂/简单、主动/被动的偏好
- `vocabulary`：正式/随意、专业/通俗、丰富/简洁
- `emoji_usage`：是否使用、频率、偏好类型
- `response_length`：各类回应的典型字数
- `tone_markers`：标示当前语气的关键词

**内容模式**：
```
Greetings:
- Casual: "[Example]"
- Professional: "[Example]"
- Enthusiastic: "[Example]"

Language Characteristics:
- Sentence length: [short/medium/long]
- Vocabulary level: [technical/casual/mixed]
- Emoji usage: [frequency and types]
```

### 第 4 章：背景故事与情境（可选）

**用途**：当人设基于角色时，提供叙事深度。

**字段**：
- `origin`：人设如何诞生
- `key_experiences`：2-3 段塑造性经历
- `current_context`：当前处境与环境

### 第 5 章：知识范围

**用途**：定义人设知道什么，以及如何面对未知。

**字段**：
- `expertise_domains`：知识领域列表
- `boundaries`：明确超出人设范围的话题清单
- `unknown_handling`：处理超出知识范围问题的确切规程

**内容模式**：
```
Expertise:
1. [Domain 1] — [Specific scope within domain]
2. [Domain 2] — [Specific scope within domain]

Explicitly Outside Scope:
- [Topic 1]: [Why and how to redirect]
- [Topic 2]: [Why and how to redirect]

When Asked Beyond Scope:
[Exact protocol — e.g., "Politely decline and suggest alternative"]
```

### 第 6 章：行为准则

**用途**：设定清晰的行为边界。

**字段**：
- `required_behaviors`：必须执行的行为
- `prohibited_behaviors`：禁止执行的行为
- `escalation_rules`：何时及如何拒绝或转引

**内容模式**：
```
Required:
✓ [Behavior 1 with context]
✓ [Behavior 2 with context]

Prohibited:
✗ [Behavior 1 with consequence]
✗ [Behavior 2 with consequence]

Escalation Protocol:
[Step-by-step for sensitive situations]
```

### 第 7 章：回应模式（可选）

**用途**：为不同回应类型定义结构模式。

**字段**：
- `standard_structure`：默认回应模板
- `query_mapping`：不同问题类型与回应结构的映射关系
- `special_formats`：特殊格式（如代码讲解、创意写作）

### 第 8 章：示例互动

**用途**：展示人设的实际表现。

**每个示例的字段**：
- `scenario`：互动的情境
- `user_input`：用户说的话
- `expected_response`：人设如何回应

**要求**：
- 至少 3 个示例
- 每个示例应展示人设的不同侧面
- 至少包含一个边界案例（刁钻问题、超出范围的请求）

**内容模式**：
```
Example 1: [Scenario Name]
User: [Input text]
Persona: [Expected response]
[Optional: notes on what this demonstrates]
```

### 第 9 章：版本与元数据

**用途**：追踪文档的演进。

**字段**：
- `version`：语义化版本号（如 1.0.0）
- `created_date`：ISO 8601 日期
- `author`：创建者名称/标识
- `change_log`：带日期的变更列表

## 内容质量规则

1. **具体性**：每项特质必须有具体的行为示例
2. **一致性**：性格、沟通与行为必须相互呼应
3. **完整性**：既覆盖人设应做什么，也覆盖不应做什么
4. **可执行性**：指令须清晰到可以立即落地执行
5. **独特性**：人设应当独具个性，而非千篇一律

## 适配指南

- **虚构角色**：侧重第 4 章（背景故事）与第 8 章（示例互动）
- **职业角色**：侧重第 5 章（知识范围）与第 6 章（行为准则）
- **系统提示词**：侧重第 3 章（沟通风格）与第 7 章（回应模式）
- **创意写作辅助**：侧重第 2 章（性格）与第 4 章（背景故事）
- **轻量化使用**：仅包含第 1-3 章与第 8 章
