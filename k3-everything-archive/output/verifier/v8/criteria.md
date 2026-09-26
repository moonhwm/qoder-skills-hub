# verifier v8 —「烧」批次收尾核验（2026-09-02）

范围：GLM 燃烧工单 W1/W2/W3 五席执行的收尾证据链。

- I1 回执齐：<输出区>/蜂群回执/P0review_GLM52{条文席,逃逸面席,用户代言席,核算席,ACK席}.md 五件在盘且非空
- I2 票型可解析：burn_20260902/results.json 五席 http=200 且三表决席 content 内 R1/R2/R3 票型可正则提取
- I3 入账与闸：蜂群消耗台账.jsonl 今日 skill=GLM燃烧工单W123 ≥5 条，当日总额 < DAILY_CAP ¥50
- I4 票册落册：表决记录册_S2026L3-01.jsonl ≥5 行（创刊+3 席+归并），每行 md5 字段 32 位 hex
- I5 零明文：上述回执/票册/本 check.py 之外产物不含 SECRETS 任一项（含 api_key 前缀扩展项）；check.py 本体豁免（v1 先例）
