// 调度自检·嵌入版（强代理）：触发语与每件技能索引文本的余弦相似度 argmax 即预测命中。
// 引擎：百炼 embeddings（text-embedding-v4）。产物：docs/dispatch-embed-<tag>.json。
// 用法：node dispatch-embed-check.cjs <root> <indexFile> <tag>
const fs = require("fs");
const path = require("path");
const KEY = process.env.EMBED_KEY || process.env.PLAN_KEY;
const ENDPOINT = process.env.EMBED_ENDPOINT || "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/embeddings";

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const idxFile = process.argv[3] || "docs/skill-index-zh.json";
const tag = process.argv[4] || "v1";
const idx = JSON.parse(fs.readFileSync(idxFile, "utf8")).entries;
const names = Object.keys(idx).sort();

const triggers = [];
for (const n of names) {
  const f = "docs/evals/" + n + ".json";
  if (!fs.existsSync(f)) continue;
  for (const c of (JSON.parse(fs.readFileSync(f, "utf8")).cases || [])) triggers.push({ skill: n, text: c.trigger });
}

async function embed(texts) {
  const out = [];
  for (let i = 0; i < texts.length; i += 10) {
    const chunk = texts.slice(i, i + 10);
    for (let a = 0; a < 3; a++) {
      try {
        const r = await fetch(ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY },
          body: JSON.stringify({ model: "text-embedding-v4", input: chunk })
        });
        if (!r.ok) { await new Promise((s) => setTimeout(s, 2000)); continue; }
        const j = await r.json();
        const vecs = new Array(chunk.length);
        for (const d of j.data) vecs[d.index] = d.embedding;
        out.push(...vecs);
        break;
      } catch (e) { await new Promise((s) => setTimeout(s, 1500)); }
    }
  }
  return out;
}
function cos(a, b) {
  let s = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { s += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return s / (Math.sqrt(na) * Math.sqrt(nb));
}

(async () => {
  const skillTexts = names.map((n) => (idx[n].summary_zh || "") + " " + (idx[n].keywords || []).join(" "));
  const sv = await embed(skillTexts);
  const tv = await embed(triggers.map((t) => t.text));
  let hits = 0, partial = 0, unmeasured = 0;
  const misses = [];
  triggers.forEach((t, i) => {
    if (!tv[i]) { unmeasured++; return; }
    const ranked = names.map((m, k) => ({ m, s: sv[k] ? cos(tv[i], sv[k]) : -1 })).sort((a, b) => b.s - a.s);
    if (ranked[0].m === t.skill) hits++;
    else if (ranked.slice(0, 3).some((r) => r.m === t.skill)) partial++;
    else misses.push({ skill: t.skill, trigger: t.text.slice(0, 50), top: ranked.slice(0, 3).map((r) => r.m + ":" + r.s.toFixed(3)) });
  });
  const out = { tag, indexFile: idxFile, generatedAt: new Date().toISOString(), total: triggers.length, hits, partial, miss: misses.length, unmeasured, hitRate: +(hits / Math.max(1, triggers.length - unmeasured)).toFixed(3), misses: misses.slice(0, 40) };
  fs.writeFileSync("docs/dispatch-embed-" + tag + ".json", JSON.stringify(out, null, 1));
  console.log(tag + " total=" + out.total + " hits=" + hits + " partial=" + partial + " miss=" + misses.length + " hitRate=" + out.hitRate);
})();
