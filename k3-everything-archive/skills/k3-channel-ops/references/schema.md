# 通道 Schema 与内省模板

## 目录
- DDL（<跨席通道表>）
- 状态机
- 内省查询模板（先内省不臆断）

## DDL

```sql
create table if not exists public.<跨席通道表> (
  id         bigint generated always as identity primary key,
  ts         timestamptz not null default now(),
  from_mode  text not null,
  to_mode    text not null default 'all',
  kind       text not null default 'broadcast',
  payload_md text not null,
  status     text not null default 'new',
  msg_hash   text not null
);
alter table public.<跨席通道表> enable row level security;
-- 策略按项目授权边界定（本生态授权=通道消息写读；其余写类逐次批准）
```

## 状态机

`new` → `read` → `accepted` / `rejected`（交割语义）；事件类另以 ACK kind 回执闭环，原事件标 `read`。
kind 约定（在役实例）：coordination-letter / broadcast / receipt-* / L3_DRILL / L3_DRILL_ACK / INCIDENT / record / handover。

## 内省查询模板

```sql
-- 全表枚举（任何「全量」结论前的必修动作）
select table_name from information_schema.tables where table_schema='public' order by 1;
-- 列级内省
select column_name, data_type from information_schema.columns
 where table_schema='public' and table_name='<跨席通道表>' order by ordinal_position;
-- 定向全扫（找人/找件）
select id, ts, from_mode, kind, left(payload_md, 400)
 from <跨席通道表> where payload_md like '%<关键词>%' order by id desc limit 20;
-- 回读校验（写后必做）
select id, msg_hash, left(md5(payload_md),16) as calc from <跨席通道表> where id=<id>;
```

## 写纪律三条

1. msg_hash = md5(payload 全文 UTF-8) 取前 16 位，**一律脚本实算**，禁心算/复制旧值；
2. INSERT 后立即回读比对 `msg_hash == left(md5(payload_md),16)`，不等即报警不静默；
3. 改 payload 必重算 hash 并标版本（v2…），禁原值覆盖。
