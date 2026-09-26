// 调度自检（零燃烧）：用 docs/evals 触发语对注册目录做召回/歧义度量。
// 方法：触发语分词后与每件技能的 keywords+summary 做命中计分；
// 判定：argmax=本件=hit；本件进前三=partial；否则 miss；并列出 top3 混淆候选。
// 产物：docs/dispatch-selfcheck.json（命中率+混淆对，供描述优化决策）。
const fs = require("fs");
const path = require("path");

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const idxFile = process.argv[3] || "docs/skill-index-zh.json";
const idx = JSON.parse(fs.readFileSync(idxFile, "utf8")).entries;
const names = Object.keys(idx).sort();

function tokens(s) {
  const out = new Set();
  for (const k of (idx[s].keywords || [])) out.add(k.toLowerCase());
  const sum = (idx[s].summary_zh || "").toLowerCase();
  out.add(sum);
  return out;
}
const corpus = {};
for (const n of names) corpus[n] = tokens(n);

function score(trigger, n) {
  const t = trigger.toLowerCase();
  let sc = 0;
  for (const k of idx[n].keywords || []) {
    if (k && t.includes(k.toLowerCase())) sc += 2;
  }
  for (const j of (idx[n].judge_hint || [])) void j;
  const sum = (idx[n].summary_zh || "");
  const grams = sum.match(/[一-鿿]{2,4}/g) || [];
  for (const g of grams) {
    if (g.length >= 2 && t.includes(g)) sc += 1;
  }
  return sc;
}

const evalsDir = "docs/evals";
const results = { generatedAt: new Date().toISOString(), hits: 0, partial: 0, miss: 0, misses: [], confusable: [] };
for (const n of names) {
  const f = path.join(evalsDir, n + ".json");
  if (!fs.existsSync(f)) continue;
  const e = JSON.parse(fs.readFileSync(f, "utf8"));
  for (const c of e.cases || []) {
    const ranked = names.map((m) => ({ m, s: score(c.trigger, m) })).sort((a, b) => b.s - a.s);
    if (ranked[0].m === n) results.hits++;
    else if (ranked.slice(0, 3).some((r) => r.m === n)) {
      results.partial++;
      results.confusable.push({ skill: n, trigger: c.trigger.slice(0, 40), top: ranked.slice(0, 3).map((r) => r.m + ":" + r.s) });
    } else {
      results.miss++;
      results.misses.push({ skill: n, trigger: c.trigger.slice(0, 60), top: ranked.slice(0, 3).map((r) => r.m + ":" + r.s) });
    }
  }
}
results.total = results.hits + results.partial + results.miss;
results.hitRate = +(results.hits / Math.max(1, results.total)).toFixed(3);
fs.writeFileSync("docs/dispatch-selfcheck.json", JSON.stringify(results, null, 1));
console.log("total=" + results.total + " hits=" + results.hits + " partial=" + results.partial + " miss=" + results.miss + " hitRate=" + results.hitRate);
