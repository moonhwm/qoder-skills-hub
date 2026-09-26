# Verifier v1 — PTrade 策略静态验收标准（300171）

适用对象：`strategy/` 下的 PTrade 策略 `.py` 文件。
判定方式：`validate_ptrade.py <file>`，exit 0 = PASS；任何 ERROR = FAIL（WARN 需评审确认可接受）。

## A. 语法与兼容性（自动）
1. 文件可被 `ast.parse(..., feature_version=5)` 解析 —— Python 3.5 语法兼容
   （禁止 f-string、walrus、海象、posonly 参数、async 推导等 3.6+ 语法）。
2. 文件后缀为 `.py`。

## B. PTrade 平台规范（自动）
3. 必选事件函数：`initialize(context)` 存在；`handle_data(context, data)` 存在
   （或已通过 `run_daily` 调度并在 initialize 中注册）。
4. 仅允许白名单三方/标准库：numpy(np)、pandas(pd)、math、datetime；
   禁止 os/sys/subprocess/requests/urllib/socket/__import__/open/eval/exec。
5. PTrade API 拼写校验：对所有函数调用名与已知 PTrade API 表做相似度匹配，
   疑似拼写错误（如 order_tagret、get_hitory）报 ERROR。
6. 标的代码格式合法：`300171.XSHE`（深交所后缀）。

## C. 策略质量（评审，人工/子代理）
7. 有明确入场/出场规则，无未来函数（信号只用当日之前的历史数据）。
8. 有资金管理：单笔风险敞口受限、100 股整手、可用资金检查。
9. 有风险控制：止损/移动止损、ST/停牌/涨跌停处理。
10. 交易成本设置（佣金/滑点）已配置。
11. 日志使用 `log.info` 等平台接口，不使用 print。
12. 创业板 300 开头 20% 涨跌停的处理正确。

## 收敛定义
- 静态校验 exit 0 且无任何 ERROR；
- 独立评审一轮无新增实质问题（仅有可选优化建议视为收敛）。
