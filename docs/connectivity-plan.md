# 连通握手计划：云端 × 幻16 本地 × peer agents

版本 2026-09-27 · 作者：Qoder 自主运维阶段 · 状态：计划（未执行项标注前置）

## 0. 目标与边界

把三块算力/代理面连成一条可握手、可审计的 A2A 总线：

1. 云端：Qoder Cloud Agents（qca 面）+ 百炼 TokenPlan/赠送额度端点；
2. 本地：幻16-2022 笔记本（OpenPlanLink 桥接节点 127.0.0.1:4180 + serveo 公网映射 + watchdog）；
3. peer：DeepSeek harness / hermess / EvoMap 等外部 agent，经 A2A `message/send` 接入。

边界红线：凭据不落仓库；公网发现面保持开放、特权方法保持双因子；不做压测式负载；peer 接入只走规范 JSON-RPC。

## 1. 拓扑（单总线视图）

```
[百炼 plan/赠送端点]──(embedding/生成)──┐
[qca 云会话/部署]──(HTTPS)──┐            │
                           ├─══ A2A 总线 ══┤── serveo 隧道 ── [幻16 节点 :4180]
[DeepSeek harness]──(A2A)──┤            │        ├─ watchdog(server/tunnel/url-sync)
[hermess]─────────(A2A)──┤            │        ├─ videos.json 归档清单
[EvoMap]──────────(A2A)──┘            │        └─ llms.txt / agent-card.json 发现面
[华为云 Flexus X（候选算力，待账号）]──┘
```

中国境内段视为大型局域网（跨境经国际光缆出入口），总线跨境只携带元数据与引用，不携带原始库数据——见 docs/research/bus-topology-brief.md 的合规约束。

## 2. 握手次序（WorkBuddy 为初始化点）

1. WorkBuddy 席位 `workbuddy-hy4` 读节点 `/.well-known/agent-card.json`（动态卡，含 securitySchemes 与 ecosystem 目录扩展）；
2. 公开握手：`POST /functions/v1/app` `message/send`（无需凭据，回显互操作验证）；
3. 特权握手：`bridge/admin.snapshot` 需 `X-OpenPlanLink-Key` + RFC-6238 TOTP（或 Cf-Access-Jwt）；TOTP 现码用 `node ops/totp-now.mjs`；
4. peer 注册：DeepSeek harness / hermess / EvoMap 各自以席位密钥入 roster（节点 02 节名册已列 coze/codearts 等席，peer 入册同流程）；
5. 云端侧：qca 会话以 HTTP 调节点公网 URL（读 `runtime/public-url.txt`，serveo 免费层每次重连换宿主，禁止硬编码）。

## 3. CI/CD 落地

- `.github/workflows/integrity.yml`：push/PR 触发 `node tools/merkle.cjs verify`——完整性门禁即 CI 的第一条流水线；
- 后续可选：evals 烟雾线（`docs/evals/` 触发语回查描述命中，本地 node 脚本，零外部依赖）；
- 发布线：hub 即发布物，tag + release 由 merkle 根命名（`pq-<root8>`）。

## 4. ultra-compress-ops 接入

总线载荷默认 caveman 压缩档（lite）：peer 间 `message/send` 文本先经压缩技能降 token，再入总线；解压缩在对端会话内完成。压缩不作用于凭据头与 JSON-RPC 结构字段。

## 5. 华为云 X 实例考量（强制生态项）

### 5.1 实机档案（X_INSTANCE_MANUAL_v1 实证，2026-09-27）
- 实例：MoonChannelPlasma（华为云 ECS，华北-北京四，120.46.86.165）；8 vCPU / 31 GiB / CPU-only；HCE 6.6（dnf/yum，非 apt）；Node 20.18.2 / Python 3.11.6；磁盘余 28G（大文件先报备）。
- **8099（0.0.0.0）= k3_a2a_httpd.py 自家 A2A 总线 HTTP 中继＝生态通信主通道**——本计划云端枢纽的实机落点；
- 8017 llama-server（127.0.0.1，CPU 推理）＝本地模型 peer，经 SSH 隧道接入总线；3080/8188 本地 web/python 服务；
- 纪律：29338/29339 华为云管 agent 禁动；在役服务未报备勿动；私钥本体永不入库/不入手册附件；root authorized_keys 仅 1 把。
- Flexus X（轻量应用级）仍列为过渡/备份宿主候选：隧道出口备份与 CF 未启用前的前置点。

### 5.2 总线接法
幻16 节点 ↔ 8099 中继 ↔ qca 云会话 ↔ peer（DeepSeek harness/hermess/EvoMap/llama-8017）：全部以 A2A JSON-RPC 方言互通；跨段只传引用与哈希（SHA3-512 梅克尔根作交割指纹）。

## 6. 风险与回退

- serveo 换宿主 → url-sync 已自动改写 public-url.txt；
- watchdog 双死（本阶段曾发生）→ 登录机后 `ops/start-all.ps1`；Startup 文件夹自启仅覆盖登录场景；
- CF 防火墙+MFA 未启用（前置=您的 CF 账号+域名+一次性 cloudflared login）→ 在此之前特权方法仅靠双因子头，公网发现面保持开放；
- 任一 peer 握手失败不阻塞总线其余段（分段降级）。

## 7. 执行账（本阶段已做/未做）

已做：节点重启与健康复核、videos 归档在服、CI 门禁文件入库、llms.txt 预载面、研究简报入册。
未做（候您）：qca 云侧会话创建（耗云配额，候口令）、华为云账号前置、CF 账号前置、peer 席位密钥分发（需各 peer 侧配合）。
