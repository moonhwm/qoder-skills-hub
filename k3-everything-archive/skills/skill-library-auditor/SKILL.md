---
name: skill-library-auditor
description: 技能库（SKILL.md 仓库）全量审计工具。当用户需要盘点/审计/复核技能库、检测中英文镜像技能对、发现共享脚本冲突、校验 SKILL.md frontmatter 规范（name 与目录一致性、YAML 结构错误、缺 license/description）、统计技能库规模，或继续"技能审计/技能排重/技能库体检"类多轮任务时使用。符号链接感知，统计可复现，解决人工逐文件读取漏统软链目录、相似度程度夸大、YAML 术语误用三大实测痛点。中文名：技能库审计员
---

# 技能库审计员（skill-library-auditor）

对技能库执行**确定性全量审计**，替代逐文件人工读取。一条命令产出：统计口径、frontmatter 问题分级清单、共享脚本冲突矩阵、镜像对候选表。

## 何时不用

- 审计**对话记录里**关于技能库的论断 → 先用本脚本跑出现状基线，再逐条 diff 论断与基线。
- 创建新技能 → 用 skill-creator。

## 核心命令

```bash
# 默认扫 /app/.agents/skills + <技能安装位>（软链感知，find -L 等价语义）
python3 scripts/audit_skill_repo.py

# 指定根目录 / 输出 JSON / 落盘 Markdown 报告
python3 scripts/audit_skill_repo.py --root <技能安装位> --json > audit.json
python3 scripts/audit_skill_repo.py --out 技能库审计报告_$(date +%F).md
```

退出码恒 0；问题以 P0/P1/P2 分级写入报告而非中断。

## 输出判读

| 输出块 | 含义 | 处置 |
|---|---|---|
| 统计 | SKILL.md 总数 / 顶层目录 / 嵌套子技能 / 缺失根 | **引用统计前先看 roots_missing**——根目录被软链挂载时人工 `find` 不带 `-L` 会漏统 |
| 共享脚本 | 同一 md5 脚本被多个技能引用 | 合并候选；改脚本时须同步所有引用方 |
| 镜像对 | 相似度 ≥0.98 逐行相同级 / ≥0.90 高度相似 / ≥0.80 镜像近似，自动标注中英文翻译镜像 | 只有"逐行相同级"才可建议直接删除其一；"高度相似"须人工 diff 独有段落后再定 |
| P0 | frontmatter 缺失/解析为列表/缺 name/缺 description | 阻塞触发，立即修 |
| P1 | name≠目录名、name 非 kebab-case | 影响路由一致性 |
| P2 | 缺 license | 规范统一 |

## 措辞纪律（人工审计实测翻车点）

1. **"逐行相同"仅用于相似度 ≥0.98**；0.80–0.98 一律写"高度相似/镜像"，否则删除建议可能误删独有内容（真实事故：humanizer-zh 对被误报"逐行相同"，实则一方多出整节内容）。
2. **frontmatter 写成 `- name:` 是"结构不合规"（YAML 列表≠映射），不是"YAML 语法错误"**——前者能被 YAML 解析器正常解析但不符合 skill 加载契约，报告措辞须区分。
3. 统计数字必须带扫描根清单与时间戳；跨会话引用旧统计前先重跑脚本核验（沙箱会重置，技能库可能已变）。
4. 镜像对候选是**候选**不是定论：脚本共享（md5 相同）是硬证据，文本高相似是软证据，报告里分开陈述。

## 资源

- `scripts/audit_skill_repo.py`：全部审计逻辑，纯标准库（有 PyYAML 时 frontmatter 解析更精确，无则降级嗅探并在 stderr 声明）。`--help` 查看参数。
