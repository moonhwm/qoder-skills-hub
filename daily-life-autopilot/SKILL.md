---
name: daily-life-autopilot
description: 每日例行生活事务自动化编排——凭证哈希链自检、通勤火车票/机票查询（美团官方通道）、POI 双通道查询（高德+百度）、每日领券、价格监控提醒。当用户要求"每日例行/每天自动执行/定时任务/通勤查票/查火车票机票/领券提醒/每日检查/龙虾KIMI每日任务/Kimi Claw 定时自动化/生活自动化"时触发。
---

# 每日生活自动驾驶（daily-life-autopilot）

把已验证的散件能力编排成"每天一键/自动跑一遍"的例行流水线。本技能只含编排逻辑与通用脚本，**零凭证内置**——凭证永远从私有凭证库注入。

## 数据与工具目录约定

| 角色 | 默认路径 | 说明 |
|---|---|---|
| 私有凭证库 | `<上传区>/credentials.env` | 唯一真源；绝不复制进技能包 |
| 哈希链账本 | `<上传区>/credential_chain.jsonl` | 完整性凭证，外发安全 |
| 凭证覆盖 | 环境变量 `DATA_DIR` | 好友环境用：置 DATA_DIR 指向自己的凭证库 |

好友/外发场景：拿到本技能的人需各自注册免费凭证（高德 lbs.amap.com / 百度 lbsyun.baidu.com / 美团 developer.meituan.com，各 1-5 分钟），写入自己的 credentials.env。详见 references/credentials.md。

## 每日流程（按序执行）

```bash
chmod +x scripts/daily_check.sh
sh scripts/daily_check.sh                                   # 基础：验链+凭证在位
sh scripts/daily_check.sh --with-travel 衡阳 西安           # + 通勤火车票（实测20s返回）
sh scripts/daily_check.sh --with-coupon                     # + 每日领券（需登录态）
```

1. **验链**：`scripts/verify_chain.py` 重放哈希链——断链即停手排查，不带病作业。
2. **凭证在位**：逐项报告缺失；用户登录态缺失时领券自动跳过。
3. **例行项**：通勤查询（美团官方）、领券、POI 查询（`scripts/poi_query.py amap|baidu "<关键词>" <城市>`）。

## 定时自动化（Kimi Claw / cron）

对 agent 说「排一个每天 X 点的例行任务」或用 add_cron_job，任务指令示例：
> 「运行 daily-life-autopilot 的 daily_check.sh --with-travel 衡阳 西安 --with-coupon，把结果摘要发我」

**注意**：cron 唤醒的是全新容器——脚本内一切路径必须用持久卷绝对路径（本技能已遵守）；容器层（/tmp、/usr/local/bin、/root）的东西都会丢，详见 references/pitfalls.md。

## 能力速查（全部实战验证过）

| 能力 | 调用 | 备注 |
|---|---|---|
| 火车票/机票/酒店 | daily_check --with-travel，或直连端点 POST mcp-open-cater.meituan.com/v1/api/voyage/openapi/query | Authorization 直放 Token，无 Bearer 前缀 |
| POI 查询 | `python3 scripts/poi_query.py amap "关键词" 城市` / `baidu ...` | 高德覆盖全；百度带评分 |
| 领券 | daily_check --with-coupon | 首次登录需 60 秒短信卡秒接力 |
| 领券提醒 | add_cron_job 每日提醒 | 免登录态的降级方案 |

## 踩坑防护

所有坑已固化在 references/pitfalls.md——新会话/好友环境先读它，能省掉一整天的试错。
