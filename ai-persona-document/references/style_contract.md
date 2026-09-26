# 样式契约：AI 人设文档

## 参考来源

- **来源类型**：仅指令型（源自专业文档最佳实践与人设定义惯例）
- **主要语言**：中文（CJK）或英文，取决于用户提问语言
- **文档类型**：层级清晰的专业结构化文档

## 字体排印体系

### 字体策略

- **CJK 内容**：全文统一使用同一款支持 CJK 的无衬线字体族。
  - 首选：`Noto Sans CJK SC`（或 `Microsoft YaHei`、`PingFang SC`、`Source Han Sans SC`）
  - 兜底：`SimHei`、`SimSun`
- **纯拉丁文内容**：使用简洁的无衬线字体族。
  - 首选：`Inter`、`Segoe UI`、`Arial` 或 `Helvetica`
- **中英混排**：全文统一使用拉丁字形集成良好的 CJK 字体（如 `Noto Sans CJK SC`、`Microsoft YaHei`）。不要在不同段落中混用纯拉丁字体与纯 CJK 字体。

### 标题层级

| 层级 | 字号 | 字重 | 用途 |
|---|---|---|---|
| 文档标题 | 18-20pt | 加粗 | 封面/页眉处的文档主标题 |
| 一级标题 | 16pt | 加粗 | 主要章节（身份、性格等） |
| 二级标题 | 13-14pt | 加粗 | 子章节（关键特质、问候模式等） |
| 三级标题 | 12pt | 加粗 | 子子章节（单项特质、示例） |
| 正文 | 11pt | 常规 | 主要内容 |
| 题注/备注 | 10pt | 常规 | 注释、元数据、变更日志条目 |

### 文字间距

- **行距**：正文 1.15-1.5
- **段距**：每段之后 6-8pt
- **标题间距**：标题前 12pt，后 6pt
- **章节间距**：主要章节之间 18-24pt

## 配色方案

### 主色

| 角色 | 颜色 | 用途 |
|---|---|---|
| 主强调色 | #2B579A（深蓝） | 章节标题、关键标签 |
| 次强调色 | #5B9BD5（中蓝） | 子标题、链接 |
| 正文文字 | #333333（近黑） | 全部正文内容 |
| 次要文字 | #666666（深灰） | 题注、元数据、备注 |
| 浅色背景 | #F5F5F5（浅灰） | 示例对话块、提示框 |
| 边框/分隔线 | #CCCCCC（中灰） | 表格边框、章节分隔线 |

### 使用规则

- 所有一级标题使用主强调色
- 二级标题使用次强调色
- 正文一律使用近黑色（#333333）
- 示例互动块使用浅灰背景（#F5F5F5），内边距 8pt
- 行为规则（应做/禁做）使用低调的左边框强调（4pt，主色）

## 页面版式

### 页边距

- 上：2.5cm（1 英寸）
- 下：2.5cm（1 英寸）
- 左：2.5cm（1 英寸）
- 右：2.5cm（1 英寸）

### 页面构成

- **扉页**（短文档可省略）：居中的标题、副标题、版本、日期
- **内容页**：文字左对齐，层级列表缩进一致
- **页眉/页脚**：页眉放文档标题（左侧），页脚放页码（居中或右侧）

### 留白

- 章节之间留白充分，以提升可读性
- 避免密集文字块——拆分为要点或结构化列表
- 适当使用表格进行特质对比或规则集合的展示

## 特殊元素的视觉处理

### 示例互动块

```
Background: #F5F5F5
Padding: 10pt all sides
Border: none or 1pt solid #E0E0E0
Label: "Example N: [Scenario Name]" in bold, secondary accent color
User input prefix: "User:" in bold
Persona response prefix: "Persona:" in bold, primary accent color
```

### 行为规则列表

```
Required behaviors (✓):
- Left border: 4pt solid #2B579A (primary accent)
- Background: none or very subtle #F0F7FF

Prohibited behaviors (✗):
- Left border: 4pt solid #CC0000 (subtle red)
- Background: none or very subtle #FFF0F0
```

### 特质卡片

```
Each trait presented as:
- Trait name: Heading 3 style
- Description: Body text, indented
- Example: Body text in italics, indented further, with label "Example:"
```

### 表格

- 用于结构化对比（如问题类型 → 回应模式的映射）
- 表头行：主强调色背景配白色文字
- 隔行：白色与极浅灰（#FAFAFA）交替
- 边框：1pt 实线 #DDDDDD
- 单元格内边距：6pt

## 分语言适配

### 中文（CJK）内容

- 使用全角标点（。，！？；：""''（）【】）
- 标点后不加多余空格
- 段落缩进：传统中文排版缩进 2em（两个汉字宽度），或采用现代排版不缩进、以段距分隔
- 编号列表：按正式程度选用中文数字（一、二、三）或阿拉伯数字（1. 2. 3.）
- 章节编号：统一使用阿拉伯数字（1., 1.1, 1.1.1）

### 英文内容

- 使用标准英文标点
- 段落不缩进（以段距分隔）
- 编号列表：阿拉伯数字（1. 2. 3.）
- 章节编号：阿拉伯数字（1., 1.1, 1.1.1）

## 输出格式细则

### DOCX 输出

- 使用内置标题样式（Heading 1、Heading 2、Heading 3）以支持导航窗格
- 项目符号与编号列表使用列表样式
- 为示例互动块与特质卡片定义自定义样式
- 启用基于标题结构的目录生成
- 页面设置：按用户偏好选 A4 或 Letter（默认 A4）

### PDF 输出

- 保留 DOCX 的全部样式属性
- 确保 CJK 字符的字体嵌入
- 如使用交叉引用，保留超链接
- 针对屏幕阅读优化（边距均衡、层级清晰）
