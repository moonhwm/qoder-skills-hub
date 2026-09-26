// 脚本注释简体汉化批处理·第二轮（宽松校验）。
// 目标：第一轮被 sameShape 严格校验拒绝的块（394 块）。
// 宽松规则：行数相等 + 注释符族相等（hash/slash/star/ps）+ 缩进差 ≤2；
// 落盘前强制回贴原缩进，并做语法后检（行首必须仍是合法注释符），否则该块跳过。
// 引擎：百炼 TokenPlan 专属端点 qwen3.6-flash，并发 2。
// 断点：.sinicize2-progress.json；台账：.sinicize2-ledger.jsonl。
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const KEY = process.env.PLAN_KEY;
const ENDPOINT = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions";
const MODEL = "qwen3.6-flash";
const CONC = 2;
const PROG = ".sinicize2-progress.json";
const LEDGER = ".sinicize2-ledger.jsonl";

const files = execSync("git ls-files -z").toString().split("\0")
  .filter((f) => /\.(py|js|cjs|mjs|ts|sh|ps1)$/.test(f) && fs.existsSync(f));

const progress = fs.existsSync(PROG) ? JSON.parse(fs.readFileSync(PROG, "utf8")) : { done: {}, stats: { blocks: 0, skipped: 0, tin: 0, tout: 0 } };

function markerOf(line) {
  const m = line.match(/^\s*(<#|#>|#!|\/\/\/|\/\/|\/\*|\*|#|rem\s)/i);
  return m ? m[1] : null;
}
function fam(line) {
  const mk = markerOf(line);
  if (!mk) return null;
  const t = mk.toLowerCase();
  if (t.startsWith("//")) return "slash";
  if (t === "<#" || t === "#>") return "ps";
  if (t === "*" || t === "/*" || t === "*/") return "star";
  return "hash";
}
function eligible(line) {
  if (/^\s*#!/.test(line)) return false;
  if (/coding[:=]/.test(line)) return false;
  const mk = markerOf(line);
  if (!mk) return false;
  const rest = line.slice(line.indexOf(mk) + mk.length);
  const letters = (rest.match(/[A-Za-z]/g) || []).length;
  if (letters < 4) return false;
  if (/^\s*https?:\/\/\S+\s*$/.test(rest)) return false;
  return true;
}
function blocksOf(lines) {
  const out = [];
  let cur = [];
  for (let i = 0; i < lines.length; i++) {
    if (eligible(lines[i])) cur.push(i);
    else { if (cur.length) out.push(cur); cur = []; }
  }
  if (cur.length) out.push(cur);
  return out;
}

const SYS = "你是代码注释翻译器。把用户给出的整行代码注释译成简体中文。要求：逐行对应，行数不变；每行的缩进与注释符（#、//、/*、*、<#、#> 等）原样保留；只译自然语言，标识符、路径、命令、参数名、URL 保持原文；语气平实，不加表情与营销腔；除译文外不输出任何内容。";

async function translate(blockText) {
  const body = JSON.stringify({
    model: MODEL,
    temperature: 0.2,
    messages: [
      { role: "system", content: SYS },
      { role: "user", content: blockText }
    ]
  });
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const r = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY },
        body
      });
      if (r.status === 429) { await new Promise((s) => setTimeout(s, 3000)); continue; }
      if (!r.ok) { await new Promise((s) => setTimeout(s, 1500)); continue; }
      const j = await r.json();
      const text = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
      const u = j.usage || {};
      return { text, tin: u.prompt_tokens || 0, tout: u.completion_tokens || 0 };
    } catch (e) {
      await new Promise((s) => setTimeout(s, 1500));
    }
  }
  return null;
}

function acceptShape(orig, trans) {
  if (orig.length !== trans.length) return false;
  for (let i = 0; i < orig.length; i++) {
    if (fam(orig[i]) !== fam(trans[i] || "")) return false;
    const io = (orig[i].match(/^\s*/) || [""])[0].length;
    const it = ((trans[i] || "").match(/^\s*/) || [""])[0].length;
    if (Math.abs(io - it) > 2) return false;
  }
  return true;
}

const queue = [];
for (const f of files) {
  if (progress.done[f]) continue;
  const lines = fs.readFileSync(f, "utf8").split("\n");
  const bs = blocksOf(lines);
  if (bs.length) queue.push({ f, lines, bs });
}

let fi = 0, changedFiles = 0;
const ledger = fs.createWriteStream(LEDGER, { flags: "a" });

function saveProgress() { fs.writeFileSync(PROG, JSON.stringify(progress)); }

async function worker() {
  while (fi < queue.length) {
    const item = queue[fi++];
    let changed = 0, skipped = 0, tin = 0, tout = 0;
    for (const idxs of item.bs) {
      const orig = idxs.map((i) => item.lines[i]);
      const res = await translate(orig.join("\n"));
      if (!res) { skipped++; progress.stats.skipped++; continue; }
      const trans = res.text.replace(/\r/g, "").split("\n");
      if (!acceptShape(orig, trans)) { skipped++; progress.stats.skipped++; continue; }
      let okAll = true;
      const applied = idxs.map((li, k) => {
        const io = (item.lines[li].match(/^\s*/) || [""])[0];
        let nl = trans[k].replace(/^\s*/, io);
        if (!/^\s*(#|\/\/|\/\*|\*|<#|#>)/.test(nl)) { okAll = false; }
        return nl;
      });
      if (!okAll) { skipped++; progress.stats.skipped++; continue; }
      idxs.forEach((li, k) => { item.lines[li] = applied[k]; });
      changed++;
      progress.stats.blocks++;
      tin += res.tin; tout += res.tout;
      progress.stats.tin += res.tin; progress.stats.tout += res.tout;
    }
    if (changed) {
      fs.writeFileSync(item.f, Buffer.from(item.lines.join("\n"), "utf8"));
      changedFiles++;
    }
    progress.done[item.f] = { changed, skipped };
    ledger.write(JSON.stringify({ f: item.f, changed, skipped, tin, tout, ts: Date.now() }) + "\n");
    if ((fi % 10) === 0) saveProgress();
    console.log("done " + fi + "/" + queue.length + " " + item.f + " changed=" + changed + " skipped=" + skipped);
  }
}

(async () => {
  const workers = [];
  for (let i = 0; i < CONC; i++) workers.push(worker());
  await Promise.all(workers);
  saveProgress();
  ledger.end();
  console.log("SUMMARY files_queued=" + queue.length + " changed_files=" + changedFiles + " blocks=" + progress.stats.blocks + " skipped=" + progress.stats.skipped + " tokens_in=" + progress.stats.tin + " tokens_out=" + progress.stats.tout);
})();
