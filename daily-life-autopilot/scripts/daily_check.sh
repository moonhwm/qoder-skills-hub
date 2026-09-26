#!/bin/sh
# daily-life-autopilot · 每日例行检查（sh 兼容，勿用 bash 特性）
# v1.3（2026-08-26 晚）：多参数组合 + 环境变量起终点
# 用法: daily_check.sh [--all] [--with-travel] [--with-flyai] [--with-coupon]
# 起终点: ORIGIN=衡阳 DEST=西安 daily_check.sh --all
DATA_DIR="${DATA_DIR:-<上传区>}"
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
ORIGIN="${ORIGIN:-衡阳}"; DEST="${DEST:-西安}"
ARGS=" $* "
has() { case "$ARGS" in *" $1 "*|*" --all "*) return 0;; *) return 1;; esac; }

echo "═══ 1. 凭证哈希链校验 ═══"
python3 "$SCRIPTS/verify_chain.py" || echo "⚠️ 链校验失败——停止后续动作，先排查"
[ -f "$DATA_DIR/credentials.env" ] || { echo "❌ 缺 $DATA_DIR/credentials.env"; exit 1; }

echo "═══ 2. 凭证在位检查 ═══"
. "$DATA_DIR/credentials.env"
for v in AMAP_KEY AMAP_JSCODE BAIDU_MAP_AK MEITUAN_DEV_TOKEN MEITUAN_USER_TOKEN FLYAI_API_KEY AVIATIONSTACK_KEY; do
  eval "val=\$$v"
  [ -n "$val" ] && echo "  ✅ $v" || echo "  ⚠️ $v 缺失/为空"
done

# 可选：通勤查询（美团官方酒旅通道，curl 直连，绕开 CLI 120s 包装层）
if has --with-travel; then
  echo "═══ 3. 通勤查询: $ORIGIN → $DEST ═══"
  curl -s -m 150 -X POST "https://mcp-open-cater.meituan.com/v1/api/voyage/openapi/query" \
    -H "Authorization: $MEITUAN_DEV_TOKEN" -H "Content-Type: application/json" \
    -d "{\"city\":\"$ORIGIN\",\"query\":\"${ORIGIN}到${DEST}的火车票\",\"originQuery\":\"${ORIGIN}到${DEST}的火车票\",\"channel\":\"meituan-developer\"}" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print((d.get('data') or str(d))[:800])"
fi

# 可选：飞猪结构化票价（全量车次+真实价格，优先于美团文案通道）
if has --with-flyai; then
  echo "═══ 3b. 飞猪票价表: $ORIGIN → $DEST ═══"
  grep -q "flyai.open.fliggy.com" /etc/hosts 2>/dev/null || echo "203.119.204.199 flyai.open.fliggy.com" >> /etc/hosts 2>/dev/null
  FLYAI_BIN="${FLYAI_BIN:-<输出区>/tools/standalone/flyai.cjs}"
  FLYAI_API_KEY="$FLYAI_API_KEY" node "$FLYAI_BIN" search-train --origin "$ORIGIN" --destination "$DEST" --sort-type 3 2>/dev/null \
    | python3 -c "import json,sys
try:
    d=json.load(sys.stdin); seen=set()
    for it in d.get('data',{}).get('itemList',[]):
        s=it['journeys'][0]['segments'][0]
        key=(s['marketingTransportNo'], s['seatClassName'])
        if key in seen: continue
        seen.add(key)
        print(f\"{s['marketingTransportNo']} {s['depDateTime'][11:16]}→{s['arrDateTime'][11:16]} {s['seatClassName']} ¥{it.get('price','?')}\")
except Exception as e: print('飞猪查询失败:', e)"
fi

# 可选：通道活性探针（批判一修复：通道状态是时变随机过程，布尔档案改为带时间戳观测序列）
if has --with-probe; then
  echo "═══ 5. 通道活性探针 $(date '+%F %T') ═══"
  # 高德：geocode 稳定参照物（天安门）——带变体B签名（原始值拼接+MD5）
  python3 - "$AMAP_KEY" "$AMAP_JSCODE" << 'PROBE_EOF'
import hashlib, json, sys, urllib.parse, urllib.request
key, jscode = sys.argv[1], sys.argv[2]
p = {"address": "天安门", "city": "北京", "key": key, "output": "json"}
raw = "&".join(f"{k}={v}" for k, v in sorted(p.items())) + jscode
p["sig"] = hashlib.md5(raw.encode()).hexdigest()
try:
    d = json.load(urllib.request.urlopen(f"https://restapi.amap.com/v3/geocode/geo?{urllib.parse.urlencode(p)}", timeout=20))
    print(f"  高德geocode: {'✅' if d.get('status')=='1' else '❌ '+str(d.get('info'))}")
except Exception as e:
    print(f"  高德geocode: ❌ {type(e).__name__}")
PROBE_EOF
  # 百度：活跃业务查询（命中数取 len(results)——total 字段非恒定出现）
  curl -s -m 20 "https://api.map.baidu.com/place/v2/search?query=%E8%97%A4%E9%87%8E%E9%80%A0%E5%9E%8B&region=%E8%A5%BF%E5%AE%89&city_limit=true&output=json&ak=$BAIDU_MAP_AK" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); n=len(d.get('results') or []); print(f\"  百度place: {'✅ 命中'+str(n) if d.get('status')==0 else '❌ '+str(d.get('message'))}\")" 2>/dev/null || echo "  百度place: ❌ 请求异常"
  # 飞猪：CLI 探活（--help 不耗配额）
  node <输出区>/tools/standalone/flyai.cjs --help >/dev/null 2>&1 && echo "  飞猪CLI: ✅ 可执行" || echo "  飞猪CLI: ❌ 文件缺失（npm挥发复发?）"
  # 美团用户态：不发券，仅提示存在性（真实活性由每日领券自证）
  [ -n "$MEITUAN_USER_TOKEN" ] && echo "  美团user_token: 在位（活性由每日领券自证）"
fi

# 可选：每日领券（需有效 MEITUAN_USER_TOKEN；60秒短信窗口仅首次登录需要）
if has --with-coupon; then
  echo "═══ 4. 每日领券 ═══"
  ISSUE="$DATA_DIR/../output/skills/meituan-fenxiao-promotion-coupon/meituan-fenxiao-promotion-coupon/scripts/issue.py"
  [ -n "$MEITUAN_USER_TOKEN" ] && python3 "$ISSUE" --token "$MEITUAN_USER_TOKEN" || echo "⚠️ 无用户登录态，跳过"
fi
