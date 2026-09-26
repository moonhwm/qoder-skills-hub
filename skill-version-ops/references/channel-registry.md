# 插件通道健康检查注册表（channel-registry）

> 每通道一行：形态｜强制调用方式｜最近实证（日期/席别/数据）｜缺口动作。
> 更新纪律：每次刷新执行后回写本表；新插件先研究（SKILL.md §三）再补行。禁止只验证不回写。

## MCP 插件（select_tools 加载最轻只读工具，调一次）

| 插件 | 握手调用 | 最近实证 | 缺口动作 |
|---|---|---|---|
| supabase | `list_projects` | 🟢 2026-09-01 雁西：2 项目 ACTIVE_HEALTHY | — |
| github | `get_me` | 🟢 2026-09-01 雁西：moonhwm（4 公开+1 私有库） | — |
| baidu-pan | `get_quota` | 🟢 2026-09-01 雁西：errno=0，总 15TB/用 2.4TB | — |
| canva | `list-brand-kits`（limit=1） | 🟢 2026-09-01 雁西：授权有效，items 空（无品牌套件） | — |
| stripe | `stripe_api_read` 最小只读 | ⚪ 未装载实测 | 涉钱护栏：写操作须秘书长显式批准 |

## CLI 插件（which + auth status）

| 插件 | 握手调用 | 最近实证 | 缺口动作 |
|---|---|---|---|
| lark | `lark-cli auth status` | 🟡 2026-09-01 雁西：bin 在位，`not_configured` | 用户跑 `lark-cli auth login` 或浏览器授权 |
| kdocs | `which kdocs-cli`；在位则先 `bash scripts/auth_restore.sh` | 🔴 2026-09-01 雁西：kdocs-cli 不在 PATH | 沙箱外安装或待环境预装；token 永不入对话/日志 |
| email | 定位 `plugins/managed/email/scripts/mail_cli.py`（多路径，勿一查即弃），再 `auth` 状态 | 🟡 2026-09-01 雁西：`/app/.agents/plugins/email/scripts/mail_cli.py` 在位，未配置邮箱 | 用户提供授权码（走安全输入，不回显不落盘） |

## agent-gw 数据源（一次最小查询；无任务登记待命，不空转）

| 插件 | 调用方式 | 最近实证 | 缺口动作 |
|---|---|---|---|
| scholar | `cd <插件根> && python3 scripts/scholar_tool.py describe`（⚠️脚本在**插件根/scripts**，非技能子目录） | 🟢 2026-09-01 雁西：describe 实测返回 API 目录（scholar_search 等） | — |
| yuandian_law | `cd <插件根> && python3 scripts/yuandian_law_tool.py describe`（同上路径坑） | 🟢 2026-09-01 雁西：describe 实测返回（yd_law_search semantic/ft_keyword 等） | — |
| tianyancha / ifind / wind-allskill / gildata-aifinmarket / caixin-* 等金融数据源 | 各自最小只读查询 | ⚪ 待命 | 金融任务触发时按域路由验证 |

## 纯技能（读 SKILL.md 首部即视为调用验证）

| 插件 | 最近实证 | 缺口动作 |
|---|---|---|
| interactive-research-report-en | ⚪ 待命（触发时读 SKILL.md 执行管线） | — |
| musepool | ⚪ 待命（设计任务前读 SKILL.md 取灵感） | — |

## 哨兵与落库锚点

- 重装窗口哨兵 cron：task_id `1a05bfef-c2b2-855f-8000-00601cbbbd68`（每日 06:40，2026-09-01 实装）
- 通报落点：Supabase `k3-api-trial.public.governance_records`（category=通报）；系列事件 EVT-20260901-SKILLREFRESH-001/002/003
