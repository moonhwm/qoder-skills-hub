# 外池压测炉细则（furnace_ops.md）

> 接 key 与上炉前、出事故时读。对应 SKILL.md §1–§3 与 §1.5。实证均出 2026-08-30 至 2026-09-05 四次战役台账。

## 一、信号码与池况判读

| 信号 | 含义 | 处置 |
|---|---|---|
| HTTP 429 + `{"code":"1113","message":"余额不足或无可用资源包"}` | GLM/智谱族池见底 | 单针实证后落选，转候选登记；禁止空转重试 |
| HTTP 401 + `{"code":"401002","message":"The API Key does not exist..."}` | 凭据服务甲 网关：key 不属此网关 | 归属探针转下一候选端点；禁止据此判 key 已死（实证 2026-09-05：同 key 在 api.deepseek.com 200 活，余额 299.98 CNY） |
| HTTP 200 `GET /models` 或 `/user/balance` | 归属实证成立 | 入座席档案；余额分 granted/topped_up 两字段抄录（治理分档见 §七） |
| `finish=length` + content 全空 + `reasoning_tokens` 顶格 | 推理族思维奔逸（deepseek-v4 系默认开思维链） | 请求体加 `thinking:{"type":"disabled"}`（实证 16,643→190 tok）或 `reasoning_effort` 档（538 tok）；补丁参数入座席档案 |
| 池况遥测（余额字段） | 各池实时余量（如 air / 4.6v / general 分池） | 每轮守窑读一次；以实数为准，票面估算不下结论（实证：估 6M 实烧越过） |
| `Cannot fork` / `pthread_create` | 全机线程耗尽 | 立即线程普查（§四），九成九是线团病 |
| 礼品池死线 | cost≡0 池有到期时刻（实证：GLM 礼赠池 09-09 死线） | 登记死线→限期目的导向燃尽→逾期未燃尽核销在案 |

## 二、候选登记模板（三件套）

```
- 候选集: <模型A>(落选:<单针证据>) / <模型B>(中选:<理由,如"同族最近信道,cost=0">) / <模型C>(在场登记,未中选:<原因>)
- 登记落点: verifier README 或等效台账，时间戳必填
```

## 三、裁定台账模板（判官结论重推导）

每判官每结论一行：`判官 | 命题 | 原数值 | 重推导值 | 裁断 | 依据`。
实证判官事故三类：①mask 空间算术错（3.09e10→8.03e10）；②结构化组合低估 100×；③bcrypt 速率把攻击者高估 7–14 倍（锚：Chick3nman 公开基准 4090/bcrypt-cost12≈1.44e3 H/s、MD5≈1.64e11 H/s）。降级替补须披露同族偏倚。

## 四、线程普查与排水（线团病法办流程）

```bash
# 普查：按进程数线程
ps -eLf 2>/dev/null | awk 'NR>1{print $2}' | sort | uniq -c | sort -rn | head
# 定位某进程线程数
ps -o nlwp= -p <PID>
```
修复= runner 每轮 join 排水（见 scripts/furnace_runner.py）；修后**连坐普检**同机其他批量进程。实证疗效：31,944 → 218 根，内存 available 翻倍。

## 五、判具设计细则

1. 关键词命中前先归一三种记号形态：LaTeX（`\exists\varepsilon_0`）/ Unicode（∃ε₀）/ 口语（存在 epsilon）。不归一直接命中会低估约一半（实证：朴素口径 54%，人工抽检近满分）。
2. 模型自评分仅参考，不进裁决；抽样人工审读每维至少 1 题。
3. 评技能「内容记忆维」时，技能原文须 RAG 注入被测上下文；缺席时模型「声明无法访问再作答」记合规。
4. 每题台账字段：`ev/id/dim/tokens/cost/chars/key_hits/self_score/ts`，压测报告引用台账不引记忆。

## 六、后台守窑纪律

- 起炉：`setsid nohup python3 runner.py > furnace.log 2>&1 < /dev/null &`，记 PID。
- 守窑：分段 sleep（≤300s/次）轮询台账 tail 与池况；禁止单调用长 sleep（504/deadline_exceeded 前科）。
- 结案：halt 事件落账 + verifier 判据 run + 报告双交付（md+docx 按项目惯例）。

## 七、新席位接入验收细则（对应 SKILL.md §1.5 装机五查）

**座席档案格式**（`<座席档案路径>`，chmod 600；`api_key` 写入后永不再动、任何输出只掩码头6…尾4）：

```json
{"version":"v1_YYYYMMDD",
 "seats":{"<seat_name>":{
   "provider_label":"", "api_key":"<永不回显全值>",
   "endpoint_candidates":["<归属探针序，实证胜者置顶>"],
   "model_candidates":["<实读 /models 抄录>"],
   "balance":{"currency":"","total":"","granted":"","topped_up":""},
   "thinking_patch":"<默认/补丁参数实证结论>", "ts":""}}}
```

- **探针序**：用户声明端点 → 同族官方端点 → 聚合网关；每端点一发 `GET /models`（最低成本），按 §一 信号码归档判读，禁止并发扫、禁止带 key 打日志。
- **治理分档映射**：`topped_up>0` → 现金池呈批线（批量燃烧前必报秘书处，联挂 <夜场件> 预算先报）；`granted>0 且 topped_up=0` → 礼品池死线纪律（§一）。两字段都抄，禁只抄 total。
- **金标准验收题**：一道短 JSON 输出题（如评分题），跑「默认 / 补丁」两式对比 tokens 与 content 是否为空；结论连同补丁参数写入档案 `thinking_patch` 字段，并落 verifier runs 轨迹。
- **不新增席位红线**：用户点名「不新增席位」时，验收只做探针+读数+档案回填，不注册新 runner 席位。
