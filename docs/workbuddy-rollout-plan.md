# WorkBuddy 生态 AI 数字员工：部署到验收全流程陪跑方案

版本 2026-09-27 · 适用：幻16 本地节点 + 华为云 X 实例（MoonChannelPlasma）+ Qoder 技能库三面协同
陪跑原则：每一步"命令→预期输出→失败回退"三件套；验收以可复现证据为准，不接受口头完成。

## 阶段 0 · 资产与凭据盘点（0.5 天）
1. 清单：节点仓库（本工作区）、技能库（github.com/moonhwm/qoder-skills-hub）、X 实例手册（GOVERNANCE/X_INSTANCE_MANUAL_v1.md）；
2. 凭据归位：百炼 plan/赠送键、OpenPlanLink 双因子（runtime/secrets.env）、X 实例私钥（仅本机，永不入库）；一律不进仓库与手册附件；
3. 验收：`grep -rE "sk-(ws|sp)-" qoder-skills-hub/` 零命中；secrets.env 在 .gitignore 等效保护下。

## 阶段 1 · 本地节点部署（0.5 天）
1. `powershell -ExecutionPolicy Bypass -File ops\start-all.ps1`；预期：三进程（watch-server/watch-tunnel/url-sync）+ `runtime/public-url.txt` 出现 serveo 宿主；
2. `curl 127.0.0.1:4180/healthz` → `{"ok":true,...}`；`curl <public>/…/.well-known/agent-card.json` → 动态卡含 securitySchemes；
3. 回退：端口被占→改 dev/server.ts 端口常量并重跑；隧道失败→读 runtime/tunnel.log 末 20 行。
4. 验收：公网 `message/send` 回确定性回执（kind:text 必填）。

## 阶段 2 · 云端枢纽对接（1 天）
1. SSH 入 X 实例（私钥本机）；`ss -lntp | grep 8099` 确认 k3_a2a_httpd.py 在役；**未报备勿动在役服务**；
2. 幻16 节点 agent-card 登记 8099 中继为 ecosystem 扩展项；qca 云会话以 HTTP 调 8099 做跨云握手；
3. llama-8017 经 SSH 隧道暴露为本地模型 peer（`ssh -L 8017:127.0.0.1:8017`）；
4. 验收：三段各一次握手回执留痕入 docs/archive-ledger.jsonl。

## 阶段 3 · 技能与调度上线（1 天）
1. 技能库 `node tools/merkle.cjs verify` 过 → 按 README 安装/注册；
2. 调度基线：`docs/evals/` 触发语抽检 ≥20 件人工过目；嵌入代理 hitRate 现状 0.659 作基线留痕；
3. 描述手术同步注册表：skill_manage patch（目录服务可用时）；不可用时留痕待窗口；
4. 验收：抽检表 + 基线数字入档。

## 阶段 4 · 安全加固（0.5 天，候用户前置）
1. Cloudflare turnkey（ops/cloudflare/）：需用户 CF 账号+域名+一次性 cloudflared login；启用后 WAF+Access(MFA) 罩 /functions/v1/app，发现面保持公开；
2. 双因子轮换：OPENPLANLINK_TOTP_SECRET 季度轮换；Server酱微信推送需用户 sendkey（secrets.env 增 SERVERCHAN_SENDKEY 后启用 ops/wechat-push 模板）；
3. 验收：MFA 挑战通过截图/回执留痕；未启用项以"前置清单"状态入档不冒充完成。

## 阶段 5 · 观测与自愈（持续）
1. watchdog 双活验证：kill 服务进程→60 秒内自启（月度演练）；
2. 梅克尔巡检：CI（.github/workflows/integrity.yml）每次 push 校验；本地周巡 `verify`；
3. 总线快照行数/回执延迟入 runtime/telemetry.jsonl（追加式）。

## 阶段 6 · 验收总闸
- 证据包：各阶段验收输出归档 docs/acceptance/<日期>/；
- 总判定：六阶段证据齐 = 验收通过；任一缺 = 阻塞项清单化，不整体冒充通过；
- 复盘：按 zijue 件诚实记录失败与未遂，全结果广播。

## 附：多库建档留痕映射（候凭据）
Supabase/Neon/ima/WPS 金山文档月之暗面文件夹：当前会话面均无可用凭据或 MCP 面（Supabase/Neon 插件已下线、kdocs 登录墙）→ 以 docs/archive-ledger.jsonl 本地总账先行，凭据到位后镜像同步；百度云盘/腾讯云函数同列候补通道。iOA 分组查询同候凭据（腾讯 iOA 控制台登录墙）。
