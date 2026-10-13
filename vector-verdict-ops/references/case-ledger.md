# 案例台账格式（verdict card ledger）

## 卡片字段（每判定一卡，append-only）

| 字段 | 含义 |
|---|---|
| version | 规则/脚本版本（判定规则改动须递增） |
| ts | UTC 时间戳 |
| pair.a_sha / pair.b_sha | 双方文本 sha256[:16]（文本本体不落台账，防敏感内容滞留） |
| channels | 在轨通道厂商名列表（如 ["bailian","zai"]）；模型/族/维度见 meta[].provider/model/family/dim_* |
| meta | 每通道元信息与事件：family、dim_registered/dim_returned/dim_drift、usage、bg_count/bg_ok、BG_INSUFFICIENT_PREFLIGHT 等 |
| per_channel | 每通道判定：IN_CANDIDATE/EDGE/OUT/UNDETERMINED |
| sims / z | 每通道相似度与 z 值（UNDETERMINED 通道为 null） |
| verdict | 会裁结论：IN/EDGE/OUT/UNDETERMINED |
| rule | 判定规则铭文（随卡携带，防规则漂移后误读旧卡） |
| card_sha | 卡片 sha256[:16] |
| prev_sha | 前卡卡 sha——哈希链，断链即台账作废待查 |

## 复核口径

- `review --ledger`：校验链完整性（chain_ok）+ 判定分布统计。
- 重审某案：取原文重新 `pair` 判一次，对比新旧卡的 verdict 与 sims 差；通道名册或规则版本不同属预期漂移，须注明。
- 台账即证据：对外引用判定结论时必须附 card_sha 与通道名册，禁口头转述。
