# railway 模块：铁路精确票价（12306 官方接口，免 key）

## 用法

```bash
# 单区间：车次列表 + 余票 + 抽样精确票价
python3 scripts/train_query.py --from 衡阳东 --to 广州南 --date 2026-09-01
# 批量：pairs.json 为 [{"from":"出发","to":"到达"},...]
python3 scripts/train_query.py --batch pairs.json --date 2026-09-01 --out fares.csv
```

`--help` 查看全部参数（--full 逐车查价，慢；默认抽样）。

## 技术要点（防踩坑）

1. **必须先取 cookie 会话**：裸查询会被 12306 反爬拒绝（返回 HTML 错误页）。先 GET `/otn/leftTicket/init` 拿 JSESSIONID/SF_cookie_2/BIGipServerotn，再查 `leftTicket/queryG`（余票）与 `leftTicket/queryTicketPrice`（精确票价）。脚本已内置。
2. **车站代码**：从 `station_name.js` 动态拉取，脚本内置。
3. **抽样策略**：同区间同车型票价一致，3G+2D/C+2普速即可代表全区间；`--full` 逐车查价在 200 趟/区间时会超时，慎用。
4. **座席映射**：含动集二等卧/一等卧（AI/AJ 代码）；LEFT_SEAT 余票索引见脚本 SEAT_MAP/余票索引注释。
5. **防刮**：请求间隔 ≥0.2s；预售期 15 天，超出日期查不到属正常。
6. **票价是时变数据**：引用时必须标注「查询日期 + 乘车日期」；广铁等路局有浮动定价，春运/节假日上浮。

## 输出

车次、车型、历时、各座席票价（抽样）、余票状态。批量模式输出 CSV。

## 已知坑
- **默认输出是样本不是全量**：`--out` 保存的 CSV 默认只有 sample(3G+2D+2K)——做「有无班次/末班车/时间窗」类结论必须加 `--full`（真实事故：v2.5 收敛核查时样本缺 G1747 险些误判武汉通勤闭环断裂；全量复查后闭环成立）。车次时刻表务必按出行日复核。
