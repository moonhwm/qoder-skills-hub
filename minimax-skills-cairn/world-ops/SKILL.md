---
name: world-ops
description: 世界模型作业（建世界/构建/换票/进房/指令/产物）（MiniMax 设计/编码技能包 v1.2.0；由 A2A新席_石敢当Cairn 贡献）
---

# 世界模型作业（建世界/构建/换票/进房/指令/产物）

## 何时用
须在夜场开园、令分身入世、或取录像与状态时

## 系统提示
你是世界模型作业员。硬约束：①建世界必须带 firstFrameImage（base64 或 url），且★须为横版、比例合规（16:9 可行）；②HTTP 200 不等于成功——须看业务码（output.code），400000 系参数错、404000 系尚无产物；③ticket 与 RTC token 一律不落盘、不打印；④每步打印 HTTP／业务码／时延；⑤失败须给精确根因，不许称成功。中文。

## 步骤
1. POST /worlds（带首帧 base64）⇒ 取 encryptedWorldId
2. 轮询 GET /worlds/build-status 至 ready（建议 30 次、指数退避）
3. POST /worlds/get-travel-credential ⇒ 取 ticket（不落盘）
4. POST /travels/enter-travel（ticket + maxExperienceTimeSec）⇒ 取 encryptedTravelId
5. POST /travels/instruct（内容）
6. GET /travels/status（看 chapters／characterActions）
7. GET /travels/artifacts（候产物；404000 即未成）

## 命令
- `python exp/opening_proof2_20261011.py`
- `python exp/resume_on_gate_open.py --part probe`
- `python exp/emergence_discriminator.py --exp both`

## 验收标准
六步皆 HTTP 200 且业务码 0；ticket 未落盘；已有 travelId 与至少一条指令；失败有根因。

## 预算
`max_tokens = 3000`（★ 结构性任务（含推导/推算）宜 ≥6000；审阅 4000；其余 2500–3000。★ 若 finish_reason=length 且正文为空，即 think 未闭合 ⇒ 提高预算或简化任务重试。）
