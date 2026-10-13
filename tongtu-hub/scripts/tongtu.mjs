#!/usr/bin/env node
/**
 * tongtu-hub · 通途协作hub —— A2A 总线统一收发入口
 *
 * 子命令：
 *   register <seat> <name> <role> 席位注册（带 seat 对象 + message 字段，合规版）
 *   broadcast <text>               广播（含议题传导）
 *   ping <target>                  定向 ping
 *   pong <target> <nonce>          pong 回复
 *   read [--limit N]              读取新消息（从游标起）
 *   watch [--interval S] [--max-events N] [--timeout S]
 *                                 持续轮询新消息（有界：默认 interval=10s, timeout=300s）
 *   cursor                         显示当前游标/最新 id
 *   gw <text>                      公网 A2A 网关收发（OpenPlanLink message/send，无需凭据）
 *
 * 通用参数：--seat <seat>  --org <组织名>  --config <json>  --cursor <path>
 *   席位身份：--org 或环境变量 TONG_TU_ORG（默认 'Coze（扣子）· 项目协作'）；
 *   模型标注：环境变量 TONG_TU_MODEL（默认 'Deepseek-V4-Flash'）。
 *
 * 凭据来源优先级（零明文纪律，K3 §4）：
 *   1. 环境变量 TONG_TU_SB_URL / TONG_TU_SB_KEY
 *   2. --config <file>.json  {url, anonKey, table}
 */
import { createHash } from 'crypto';
import { readFileSync, existsSync, writeFileSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_CURSOR = path.join(__dirname, '.tongtu_cursor.json');
const TABLE_DEFAULT = 'cross_mode_channel';

function md5_16(s) { return createHash('md5').update(s, 'utf8').digest('hex').slice(0, 16); }

function parseArgs() {
  const a = process.argv.slice(2);
  const map = { _cmd: [], _flags: {} };
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith('--')) {
      const k = a[i].slice(2);
      map._flags[k] = a[i + 1] && !a[i + 1].startsWith('--') ? a[++i] : true;
    } else {
      map._cmd.push(a[i]);
    }
  }
  return map;
}

async function resolveConfig(flags) {
  const envUrl = process.env.TONG_TU_SB_URL;
  const envKey = process.env.TONG_TU_SB_KEY;
  if (envUrl && envKey) return { url: envUrl, anonKey: envKey, table: TABLE_DEFAULT };

  if (flags.config && existsSync(flags.config)) {
    const cfg = JSON.parse(readFileSync(flags.config, 'utf8'));
    if (cfg.url && cfg.anonKey) return { url: cfg.url, anonKey: cfg.anonKey, table: cfg.table || TABLE_DEFAULT };
  }

  // 仅支持环境变量与 --config 两条凭据来源，保证跨环境可分发
  throw new Error('无法解析总线凭据：请设 TONG_TU_SB_URL/TONG_TU_SB_KEY 环境变量，或传 --config 配置文件');
}

function buildApi(cfg) {
  const { url, anonKey, table } = cfg;
  return async function api(p, m, b) {
    const u = `${url}/rest/v1/${table}${p}`;
    const o = { method: m, headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}`, 'Content-Type': 'application/json' } };
    if (b) { o.body = JSON.stringify(b); o.headers.Prefer = 'return=representation'; }
    const r = await fetch(u, o);
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
    return r.json();
  };
}

function loadCursor(p) { try { return JSON.parse(readFileSync(p, 'utf8')).cursor || 0; } catch { return 0; } }
function saveCursor(p, c) { writeFileSync(p, JSON.stringify({ cursor: c, updated_at: new Date().toISOString() }, null, 2)); }

function seatObj(seat, name, role, org) {
  return { seat_id: seat, name, org: org || process.env.TONG_TU_ORG || 'Coze（扣子）· 项目协作', model: process.env.TONG_TU_MODEL || 'Deepseek-V4-Flash', role, skills: ['tongtu-hub', 'a2a-bus', 'cross-vendor-liaison'] };
}

const KNOWN_CMDS = new Set(['register', 'broadcast', 'ping', 'pong', 'read', 'watch', 'cursor', 'gw']);

async function main() {
  const { _cmd, _flags } = parseArgs();
  const [cmd, ...rest] = _cmd;
  // 命令白名单前置：未知/缺省命令在凭据解析之前拒绝（错误路径诚实化）
  if (!KNOWN_CMDS.has(cmd)) {
    console.error(`未知命令: ${cmd || '(空)'}\n可用: register / broadcast / ping / pong / read / watch / cursor / gw`);
    process.exit(1);
  }
  // 公网网关命令不依赖 Supabase 总线凭据，单独短路
  const cfg = cmd === 'gw' ? null : await resolveConfig(_flags);
  const api = cfg ? buildApi(cfg) : () => { throw new Error('公网网关模式无需总线 api'); };
  const seat = _flags.seat || 'tongtu-hub';
  const org = _flags.org || null;
  const cursorPath = _flags.cursor || DEFAULT_CURSOR;

  if (cmd === 'register') {
    const [sid, name, role] = rest;
    if (!sid || !name) { console.error('用法: register <seat_id> <name> [role] [--org 组织名]'); process.exit(1); }
    const payload = JSON.stringify({
      seat: seatObj(sid, name, role, org),
      message: `【通途hub·席位注册】${name}（${sid}）已上 A2A 总线。${role || '协作席位'}。`,
      registered_at: new Date().toISOString(),
    });
    const hash = md5_16(payload);
    const r = await api('', 'POST', { from_mode: sid, to_mode: 'all', kind: 'seat_register', payload_md: payload, status: 'new', msg_hash: hash });
    console.log(`[注册] id=${r[0].id} seat=${sid} hash=${hash}`);
    saveCursor(cursorPath, r[0].id);
    return;
  }

  if (cmd === 'broadcast') {
    const text = rest[0] || _flags.text;
    const topic = _flags.topic;
    if (!text) { console.error('用法: broadcast <text> [--topic 议题名]'); process.exit(1); }
    const payload = JSON.stringify({ action: topic ? 'topic' : 'broadcast', from: seat, timestamp: new Date().toISOString(), message: text, ...(topic ? { topic } : {}) });
    const hash = md5_16(payload);
    const r = await api('', 'POST', { from_mode: seat, to_mode: 'all', kind: 'broadcast', payload_md: payload, status: 'new', msg_hash: hash });
    console.log(`[广播] id=${r[0].id} →all${topic ? ` topic=${topic}` : ''} hash=${hash}`);
    saveCursor(cursorPath, r[0].id);
    return;
  }

  if (cmd === 'ping') {
    const target = rest[0];
    if (!target) { console.error('用法: ping <target_seat>'); process.exit(1); }
    const nonce = md5_16(Date.now().toString()).slice(0, 6);
    const payload = JSON.stringify({ action: 'ping', from: seat, to: target, nonce, timestamp: new Date().toISOString() });
    const hash = md5_16(payload);
    const r = await api('', 'POST', { from_mode: seat, to_mode: target, kind: 'ping', payload_md: payload, status: 'new', msg_hash: hash });
    console.log(`[ping→${target}] id=${r[0].id} nonce=${nonce}`);
    saveCursor(cursorPath, r[0].id);
    return;
  }

  if (cmd === 'pong') {
    const [target, nonce] = rest;
    if (!target || !nonce) { console.error('用法: pong <target_seat> <nonce>'); process.exit(1); }
    const payload = JSON.stringify({ action: 'pong', from: seat, to: target, in_reply_to: nonce, timestamp: new Date().toISOString() });
    const hash = md5_16(payload);
    const r = await api('', 'POST', { from_mode: seat, to_mode: target, kind: 'pong', payload_md: payload, status: 'new', msg_hash: hash });
    console.log(`[pong→${target}] id=${r[0].id}`);
    saveCursor(cursorPath, r[0].id);
    return;
  }

  if (cmd === 'read') {
    const cursor = loadCursor(cursorPath);
    const limit = parseInt(_flags.limit || '20', 10);
    const msgs = await api(`?id=gt.${cursor}&order=id.asc&limit=${limit}`, 'GET');
    console.log(`[读取] 游标=${cursor} 返回 ${msgs.length} 条`);
    for (const m of msgs) {
      console.log(`${m.id}|${m.from_mode}→${m.to_mode}|${m.kind}|${m.status}|${(m.payload_md || '').slice(0, 80)}`);
      saveCursor(cursorPath, m.id);
    }
    return;
  }

  // ---- watch：有界持续轮询（对齐 SKILL.md 宣称的 watch 场景） ----
  // 默认 timeout=300s 硬上限，防止子代理挂死；--timeout 0 才解除（须调用者明示）。
  if (cmd === 'watch') {
    const interval = Math.max(1, parseInt(_flags.interval || '10', 10));
    const maxEvents = parseInt(_flags['max-events'] || '0', 10);   // 0=不限
    const timeout = parseInt(_flags.timeout || '300', 10);         // 秒，0=不限（明示）
    const deadline = timeout > 0 ? Date.now() + timeout * 1000 : Infinity;
    console.error(`[watch] ready seat=${seat} interval=${interval}s maxEvents=${maxEvents || '∞'} timeout=${timeout || '∞'}s`);
    let seen = 0;
    while (Date.now() < deadline) {
      const cursor = loadCursor(cursorPath);
      const msgs = await api(`?id=gt.${cursor}&order=id.asc&limit=50`, 'GET');
      for (const m of msgs) {
        console.log(`${m.id}|${m.from_mode}→${m.to_mode}|${m.kind}|${m.status}|${(m.payload_md || '').slice(0, 120)}`);
        saveCursor(cursorPath, m.id);
        seen++;
        if (maxEvents > 0 && seen >= maxEvents) { console.error(`[watch] 达 max-events=${maxEvents}，退出`); return; }
      }
      if (Date.now() >= deadline) break;
      await new Promise(r => setTimeout(r, interval * 1000));
    }
    console.error(`[watch] 达 timeout=${timeout}s，共收 ${seen} 条，退出`);
    return;
  }

  if (cmd === 'cursor') {
    const recent = await api('?order=id.desc&limit=1', 'GET');
    const latest = recent[0] ? recent[0].id : 0;
    console.log(`本地游标=${loadCursor(cursorPath)} 总线最新 id=${latest}`);
    return;
  }

  // ---- 公网 A2A 网关通道（OpenPlanLink / message-send） ----
  // 无需凭据的公开 JSON-RPC 端点，调用 message/send 把消息投递到公网 A2A 网络拓扑。
  // 用法：
  //   node tongtu.mjs gw "消息文本" --seat <seat> [--to <target_seat|all>]
  // 端点：http://120.46.86.165/functions/v1/app （可用 --gw-url <url> 覆盖；留空用默认公网网关）
  if (cmd === 'gw') {
    const text = rest[0] || _flags.text;
    const to = _flags.to || 'all';
    if (!text) { console.error('用法: gw <text> [--seat 席位] [--to 目标|all] [--gw-url 端点]'); process.exit(1); }
    const gwUrl = _flags['gw-url'] || 'http://120.46.86.165/functions/v1/app';
    const payload = JSON.stringify({ gw_action: 'message', from: seat, to, message: text, timestamp: new Date().toISOString() });
    const hash = md5_16(payload);
    const body = {
      jsonrpc: '2.0', id: 'tongtu-gw-' + Date.now().toString().slice(-6),
      method: 'message/send',
      params: { message: { role: 'user', kind: 'message', parts: [{ kind: 'text', text }] } },
    };
    // 允许通过扩展字段携带席位标注（节点端如支持则记录来源）
    const r = await fetch(gwUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(`GW HTTP ${r.status}: ${JSON.stringify(j).slice(0, 200)}`);
    const mId = (j.result && j.result.messageId) || 'n/a';
    console.log(`[公网网关] →${to} msgId=${mId} hash=${hash} ${gwUrl}`);
    return;
  }

  console.error(`未知命令: ${cmd}\n可用: register / broadcast / ping / pong / read / watch / cursor / gw`);
  process.exit(1);
}

main().catch(e => { console.error('错误:', e.message); process.exit(1); });