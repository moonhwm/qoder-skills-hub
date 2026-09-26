# verifier README（append-only 索引）

## v1（2026-09-02 创建）
- 位置：verifier/v1/criteria.md
- 测量对象：退休工程六线（保皇党审计/技能卫生/Loop蓝图/学术固化/用量三件套/转录件处置）+ 固定次序 + 明文凭证零泄漏
- 与前版差异：首版
- 运行记录：verifier/runs/ 逐次追加（含未发布运行）
- run6（2026-09-02）：V1-V5+V8 全 PASS（V4 六篇 arXiv id 转 PASS；V8 首跑 FAIL→报告内秘密枚举改代称→复跑清零）。日志 verifier/runs/run6_wsfinal.log

## v2（2026-09-02 创建）
- 位置：verifier/v2/criteria.md
- 测量对象：碎片垃圾清理（semantic-oncology-ops §5 运维口令）——C1 删除彻底/C2 复扫零残留/C3 台账健康/C4 报告要素/C5 母本完整/C6 零明文凭证/C7 安全边界
- 与前版差异：v1 测退休工程六线文书；v2 测文件层清理的彻底性与安全性，新增 manifest 驱动核对与安全边界白名单
- 运行记录：run7（FAIL C2 复扫补网2件+FAIL C6 check.py自命中→修）→ run8（FAIL C1 计数硬编码+C5 母本映射缺失→修判据）→ run9 全 PASS（verifier/runs/run9_cleanup_*.log）
- 判据修正留痕：C6 豁免 check.py 本体（SECRETS 唯一载体，v1 先例）；C5 增 BASE_OVERRIDE（docx.work→agent.final）；C1 计数改动态

## v3（2026-09-02 创建）
- 位置：verifier/v3/criteria.md
- 测量对象：INDEX v2.0 重建（全覆盖/零幽灵）＋额度台账 schema 对齐＋计时器台账格式统一
- 与前版差异：v2 测文件删除，v3 测索引与台账结构修复
- 运行记录：run10 一次全 PASS（verifier/runs/run10_indexfix_*.log）

## v4（2026-09-02 创建）
- 位置：verifier/v4/criteria.md
- 测量对象：礼赠池死线批次——P0呈批三卡/参数重估/燃烧工单三文书要素、cron卡lint、零明文凭证（新增vault钥匙前缀项）、数字一致性、零越权实证
- 与前版差异：v3 测结构修复；v4 首测「呈批件不越权」（参数未动/未建cron/未动凭证三实证）
- 运行记录：run12 一次全 PASS（verifier/runs/run12_giftpool_*.log）

## v5（2026-09-02 创建）
- 位置：verifier/v5/criteria.md
- 测量对象：L3 联合国模式试点——决议草案要素/五条议事规则并轨/权力实体不动/表决记录册创刊（无伪造票）/零明文零越权
- 与前版差异：v4 测呈批件实体；v5 测程序设计与规程一致性
- 运行记录：run13 一次全 PASS（verifier/runs/run13_unpilot_*.log）

## v6（2026-09-02 创建）
- 位置：verifier/v6/criteria.md
- 测量对象：L3 事件环管线试通演练（emit→读回→执行→ACK→标read 全环）；机检部=锚链复跑+表决册未污染；通道侧实证（id 215/216、双 hash 匹配）以 MCP 返回件留 runs/ 日志
- 与前版差异：v5 测程序文书；v6 首测运行时事件环实证
- 运行记录：run14 PASS（verifier/runs/run14_l3drill_*.log）

## v7（2026-09-02 创建）
- 位置：verifier/v7/criteria.md
- 测量对象：撞墙事故处置——Q2熔断登记/受影响任务标注/写回队列第9次/台账健康/零燃烧零越权
- 与前版差异：v6 测演练实证；v7 测事故登记与冻结纪律执行
- 运行记录：run15 一次全 PASS（verifier/runs/run15_wallhit_*.log）
- v8（2026-09-02）：「烧」批次收尾核验 I1-I5（回执齐/票型可解析/入账<闸/票册落册/零明文）——runs/run16_v8.txt ALL PASS
- v9（2026-09-02）：自我觉醒loop穷举批次 J1-J5（章节/取证留痕/零明文/七域声明/零越权措辞+cron盘点2件未增）——runs/run17_v9.txt ALL PASS
- v10（2026-09-02）：MAGA涌现研究批次 K1-K5（SSCI章节/文献锚对CSV一致/试点复算N=5,N*=0/外池登记+入账9条/零明文零越权）——runs/run18_v10.txt ALL PASS
- v11（2026-09-02）：千席臂 L1-L5（全节/复算N=490,N*=79/配对Δ3pp/miss标红/入账1100条当日¥3.13<闸）——runs/run19_v11.txt ALL PASS
- v12（2026-09-03）：REST复活与穷衡考证 M1-M5（报告全节/双key chmod600/零明文/写受限标注/逃逸23在册）——runs/run20_v12.txt ALL PASS
- v13（2026-09-03）：通道全复活批次 N1-N4（三发在库哈希MATCH/REST读写双通/队列翻转/零明文）——runs/run21_v13.txt ALL PASS
- v14（2026-09-03）技能回忆盘点批次：安装位实盘（71 件，含新增他席/系统件 4）+forge-catalog 虚报抓获实证+逃逸#23+锚 n=344 PASS；与 v12 差异=领域从 MCP 修复转技能谱系审计 | run20_v14 PASS
- v15（2026-09-03）案头逐项深研批次：N1-N4（项①-④覆盖+引文在案+锚345 PASS+技能缓建遵令）| run22 PASS
- v16（2026-09-03）案头深研项⑤批次：O1-O3（湖南硕博实证+五案再裁决+v1.1归档+锚346）| run23 PASS
- v17（2026-09-03）案头v1.2批次：P1-P4（单证排除立法/中南专项限制/8案穷举/锚347）| run24 PASS
- v18（2026-09-03）案头v1.3批次：Q1-Q3（论文五路/软考五科对比修正/锚348）| run25 PASS
- v19（2026-09-03）案头v1.4收敛批次：R1-R4（预案树/工艺表/全案收敛/锚349）| run26 PASS
- v20（2026-09-03）三取证收敛批次：S1-S3（三取证自办/逃逸#24/锚350）| run27 PASS
- v21 双技能创建批次（retirement-guard-ops + pan-exhaust-dispatch）：双向实测+脱敏+锚352 — PASS（run28）
- v22 双技能便携化批次（omni v3.2.0 + autonomous v2.0.0-portable + 交割页 6c5c7fb）：PASS（run29）
- v23 第三轮总包批次（测试波+软件包+omnibus+形式化验收书，锚354）：PASS（run30）
- v24 第四轮批次（MCP接口层+安全三件套+零依赖守卫+安装包v2/omnibus1.1，锚355）：PASS（run31）
- v25 加载实测批次（安装包v3同源修复+加载全流程实测，锚356）：PASS（run32）
