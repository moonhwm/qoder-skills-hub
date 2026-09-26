// 技能交叉引用图（本地计算，零 API 消耗）。
// 边来源：① 关键词交集（docs/skill-index-zh.json）；② 描述中直呼他件技能名。
// 产物：docs/skill-graph.json（nodes + edges + 度排名），供调度侧做邻接提示。
const fs = require("fs");
const path = require("path");

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const idx = JSON.parse(fs.readFileSync("docs/skill-index-zh.json", "utf8")).entries;
const names = Object.keys(idx).sort();
const kw = {};
for (const n of names) kw[n] = new Set((idx[n].keywords || []).map((k) => k.toLowerCase()));

function frontmatter(p) {
  const s = fs.readFileSync(p, "utf8");
  const m = s.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return {};
  const o = {};
  for (const line of m[1].split(/\r?\n/)) {
    const mm = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (mm) o[mm[1]] = mm[2].trim().replace(/^"([\s\S]*)"$/, "$1");
  }
  return o;
}
const fullDesc = {};
for (const n of names) {
  try { fullDesc[n] = (frontmatter(path.join(n, "SKILL.md")).description || "") + " " + (idx[n].summary_zh || ""); } catch (e) { fullDesc[n] = idx[n].summary_zh || ""; }
}

const edges = {};
function addEdge(a, b, kind) {
  if (a === b) return;
  const k = a < b ? a + "|" + b : b + "|" + a;
  (edges[k] = edges[k] || { a: k.split("|")[0], b: k.split("|")[1], kinds: [] });
  if (!edges[k].kinds.includes(kind)) edges[k].kinds.push(kind);
}

for (let i = 0; i < names.length; i++) {
  for (let j = i + 1; j < names.length; j++) {
    const a = kw[names[i]], b = kw[names[j]];
    let inter = 0;
    for (const k of a) if (b.has(k)) inter++;
    if (inter >= 1) addEdge(names[i], names[j], "kw" + inter);
  }
}
for (const n of names) {
  const desc = fullDesc[n];
  for (const m of names) {
    if (m !== n && desc.includes(m)) addEdge(n, m, "mention");
  }
}

const deg = {};
for (const n of names) deg[n] = 0;
const el = Object.values(edges).map((e) => { deg[e.a]++; deg[e.b]++; return { a: e.a, b: e.b, kinds: e.kinds }; });
const top = names.slice().sort((x, y) => deg[y] - deg[x]).slice(0, 15).map((n) => ({ name: n, degree: deg[n] }));

const out = {
  generatedAt: new Date().toISOString(),
  method: "关键词交集≥2 或 摘要/关键词直呼件名；本地计算零 API 消耗",
  nodeCount: names.length,
  edgeCount: el.length,
  topHubs: top,
  edges: el
};
fs.writeFileSync("docs/skill-graph.json", JSON.stringify(out, null, 1));
console.log("nodes=" + names.length + " edges=" + el.length + " top=" + JSON.stringify(top.slice(0, 5)));
