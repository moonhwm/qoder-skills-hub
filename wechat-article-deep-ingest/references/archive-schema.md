# 归档 Schema（archive-schema）

> v1.0 ｜ 2026-08-25 ｜ 修改人：Orchestrator（Kimi K3）

## §1 目录树（自主归档）
```
<archive_root>/                        # 默认 <输出区>/<项目名>/wx_archive/
├── inbox.jsonl                        # 准公众号范式收件箱
├── articles/                          # 正文缓存
│   └── <slug>/                        # 结构化命名，见§2
│       ├── <slug>.md                  # 主缓存（结构化 markdown）
│       ├── <slug>.docx                # md2docx 转换（可选）
│       ├── <slug>.pdf                 # 可选
│       └── <slug>.snapshot.json       # 快照：原始抓取元数据+首段+提取时间
├── pointers.csv                       # 结构化指针（scripts/pointer_csv.py 管理）
├── batches/                           # 批次报告（含元认知自检+待复核问题）
│   └── batch-YYYYMMDD-NN.md
└── INDEX.md                           # 归档总索引（追加式）
```

## §2 结构化命名（slug）
`<主题词>_<来源号>_<发表日期>` —— 主题词=文章核心对象拼音/英文缩写（如 jiangsu-15th5y、nanjing-industry）；日期 unknown 时标 `nd`。例：`jiangsu-15th5y_singlewell_2026`。
命名由 scripts/archive_namer.py 生成，人工可覆写。

## §3 主缓存 md 头（七元组铁律4落点）
```markdown
---
title: <原文标题>
account: <公众号名>
pub_date: <发表日期|unknown>
fetch_date: <YYYY-MM-DD>
url: <原文链接>
slug: <slug>
channel_grade: <C0-C4>  proj_grade: <A/S/B/C/D/E/P>
promo_flag: <yes沥乾/no>
three_state: <P规划/L落地/U升级/NA>
limitations: <局限一句话>
applicability: <适用度一句话>
skill_version: wechat-article-deep-ingest vX.Y
---
```

## §3.5 snapshot.json 必填字段（v1.1）
slug / url / fetch_tool / fetch_ts / status / title / account / **account_id(ghid)** / **author_field** / **pub_date_meta（原始 ct+换算值）** / **char_count** / **img_count** / tail_marker / **completeness_check（js_content 比对方法+结论）** / notes。
通道 M 供数据，本 schema 强制落盘；缺字段须写明原因。

## §4 pointers.csv schema（结构化指针）
列：`slug,title,account,pub_date,fetch_date,url,channel_grade,proj_grade,promo_flag,three_state,region,industry_tags,engineering_clue,trace,archive_path,conf,notes`
- `industry_tags` 从受控词表取：稀土/黑色金属/有色金属/能源/新兴产业/生物医药/集成电路/人工智能/人文风貌/其他（可扩展）
- `trace`=招股书/年报回溯检索词（见 source-grading.md §4）
- 只进指针的行必须过沥干（§2）或标 `conf=C`

## §5 自主归档纪律
- 每篇摄取成功即落盘四件套中至少 md+snapshot.json；docx/pdf 按需（用户要或交付要）。
- INDEX.md 每次追加一行：slug|标题|日期|级别|一句话。
- 归档失败（写入错误）与抓取失败分列登记，禁止混淆。

## §6 案例库（v1.2，铁律6）
```
<archive_root>/cases/
├── case_<slug>.json      # 每篇一案：结构化判定全记录（见 schema）
├── cases_index.csv       # 机读索引（case_builder.py 生成）
└── cases.py              # 人可读聚合（自动生成，含每案注释，可直接 import 或阅读）
```
case_<slug>.json schema：
{slug, title, account, pub_date, url, 判定: {channel_grade, proj_grade, promo_flag, three_state, p_subtype, slogan_signals[], track_record{}, p2l_findings[]}, 关键事实出列[]（四要素齐全才入）, 批判要点[], 局限[], 待复核问题[], 修改痕迹[{by,date,change}]}
诚实记录纪律：判定依据不足的字段写 null+原因；案例允许后续追加（修改痕迹逐条留痕）；cases.py 由脚本从 JSON 聚合再生成，人只读不改。
