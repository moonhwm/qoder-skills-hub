# amap 模块：高德路径规划（可选 key，优雅降级）

## 用法

```bash
export AMAP_WEBSERVICE_KEY=<你的key>
python3 scripts/route_planning.py drive   --from 衡阳东站 --to 广州南站   # 驾车
python3 scripts/route_planning.py transit --from 衡阳东站 --to 广州南站   # 公交
# 子命令：geocode / drive / transit / walk / bike（子命令在前，非 --mode 参数）
```

- 内置 geocode（地名→坐标）→ 路径规划两步
- **无 key 时**：exit code = 2 并打印申请指引（高德开放平台 → 控制台 → 应用管理 → 创建 Web服务 类型 key，免费额度足够个人使用），不硬失败、不报错堆栈

## 能力边界

- 高德**不提供**铁路/航班票价（已实测）——票价查 railway/flight 模块
- 适合：门到门接驳段（家→车站、车站→单位）的驾车/公交时间与距离，供 commute 模块四核算使用
- 距离/时间为规划值，标 conf=estimated；高峰拥堵按 +20~30% 修正
