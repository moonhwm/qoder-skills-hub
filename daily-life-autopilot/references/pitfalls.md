# 踩坑记录（2026-08-26 实战固化，按价值排序）

## 1. 沙箱容器层不持久（最痛）

shell 每次调用都是新容器：`/tmp`、`/usr/local/bin`、`/root` 全部挥发，只有 `<工作区根>` 持久。
→ 一切工具/数据装到 `<输出区>/` 或 `<上传区>/`，用绝对路径调用。
→ 美团登录态在 `/root/.xiaomei-workspace/`——登录后**同一调用内**立即捞出 token 入凭证库。

## 2. 美团短信登录双坑（领券技能）

- 坑A 设备指纹：auth.py 的 device_token = MD5(seed+毫秒+随机数)，发码与验码跨容器时指纹漂移 → SMS_VERIFY_CODE_ERROR。**修复：发码前预置固定 dt 到 auth_tokens.json**（`{"meituan-c-user-auth":{"device_token":"<固定值>"}}`）。
- 坑B 验证码 60 秒硬窗口：人工接力须 30 秒内完成（实测 27 秒成功）。
- auth_tokens.json 键名：`meituan-c-user-auth`。
- 领券：`scripts/issue.py --token <user_token>`；历史券查询走 auth.py 其他子命令。

## 3. 美团酒旅 CLI 的 120s 包装层陷阱

`ht-ai query` 内嵌 axios timeout=120s，服务端慢时一律包装成"请求超时，请稍后重试"（E_API_ERROR），**掩盖真实状态**。
→ 绕过 CLI 直连：`POST https://mcp-open-cater.meituan.com/v1/api/voyage/openapi/query`，header `Authorization: <Token>`（无 Bearer），body `{"city","query","originQuery","channel":"meituan-developer"}`，curl -m 150。实测 20.65s 返回真实数据。

## 4. 高德签名变体仲裁

官方文档对"签名时 value 是否 urlencode"表述含糊。实测：**变体B 原始值拼接**才通过（A/C 编码拼接均 INVALID_USER_SIGNATURE）。`sig = md5("&".join(f"{k}={v}" for k,v in sorted(params.items())) + jscode)`。

## 5. 共享 JS key 行为模型

高德页面暴露的共享 JS key：place/text 在白名单内（共享日配额，当日尽次日零点重置），geocode 等端点 USERKEY_PLAT_NOMATCH 直拒。自用务必注册自有 key。

## 6. 美团/点评 web 风控层级（勿冲）

- dpurl.cn 短链：App 专用，桌面 404
- 店铺主页/价格/评论：登录墙+spiderindefence 滑块（IP+行为级，stealth 无效）
- 蜘蛛 UA：登录墙（白名单已收紧）
- 匿名可读面：m.dianping.com/shopshare/（店铺状态壳）、/shop/{id}/photos（相册）
- 正规入口：developer.meituan.com 个人开发者（本技能已接入）

## 7. 高德/百度地图 web 端

SPA 渲染超时（obscura 30s 拿不到）、service API 有阿里 punish、百度老接口 need_recaptcha 循环。
→ 唯一通道：官方开放平台 API（见 credentials.md）。

## 8. 凭证传递必须文字版

截图里等宽字体的 l/i/I/1 无法区分（百度 AK 首打失败根因）。凭证一律复制粘贴文字。

## 9. 数据源强度分级（研究路径通用）

T0 硬墙：美团/点评 web 价格与主页｜T1 低效：本地宝（空壳）、360地图、高德/百度 web SPA｜T2 金矿：消费保/黑猫（投诉含实付金额）、安居客/雪球 UGC（评价带门市价）、值值值/慢慢买/什么值得买（历史价格曲线）、高德/百度/美团官方开放平台 API｜T3 基座：web_search 关键词轮换（永远先行）。
