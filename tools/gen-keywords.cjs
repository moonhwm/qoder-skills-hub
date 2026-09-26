// 技能检索增强批：为 91 件技能生成中文检索关键词与一句话摘要。
// 引擎：百炼 plan 端点 qwen3.6-flash，并发 2，失败回退为描述截断。
// 产物：docs/skill-index-zh.json（供搜索/调度侧消费）。
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const KEY = process.env.PLAN_KEY;
const ENDPOINT = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions";
const MODEL = "qwen3.6-flash";
const CONC = 2;

const dirs = fs.readdirSync(".").filter((d) => {
  try { return fs.statSync(d).isDirectory() && fs.existsSync(path.join(d, "SKILL.md")); } catch (e) { return false; }
}).sort();

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

const items = dirs.map((d) => {
  const o = frontmatter(path.join(d, "SKILL.md"));
  return { name: d, desc: (o.description || "").slice(0, 900) };
});

let tin = 0, tout = 0, failed = 0;

async function gen(item) {
  const body = JSON.stringify({
    model: MODEL,
    temperature: 0.3,
    messages: [
      { role: "system", content: "你是技能检索索引器。输入为技能名与描述。输出严格 JSON：{\"keywords\":[6至10个检索关键词，简体中文为主、可含必要英文术语],\"summary_zh\":\"不超过60字的一句话简体中文摘要\"}。只输出 JSON。" },
      { role: "user", content: "name: " + item.name + "\ndescription: " + item.desc }
    ]
  });
  for (let a = 0; a < 2; a++) {
    try {
      const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY }, body });
      if (!r.ok) { if (r.status === 429) await new Promise((s) => setTimeout(s, 3000)); continue; }
      const j = await r.json();
      tin += (j.usage && j.usage.prompt_tokens) || 0;
      tout += (j.usage && j.usage.completion_tokens) || 0;
      const t = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
      const mm = t.match(/\{[\s\S]*\}/);
      if (!mm) continue;
      const o = JSON.parse(mm[0]);
      if (Array.isArray(o.keywords) && typeof o.summary_zh === "string") return o;
    } catch (e) { await new Promise((s) => setTimeout(s, 1500)); }
  }
  failed++;
  return { keywords: [], summary_zh: item.desc.slice(0, 60) };
}

(async () => {
  const out = { generatedAt: new Date().toISOString(), model: MODEL, entries: {} };
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const it = items[i++];
      const r = await gen(it);
      out.entries[it.name] = r;
      if (i % 10 === 0) console.log("progress " + i + "/" + items.length);
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));
  fs.mkdirSync("docs", { recursive: true });
  fs.writeFileSync("docs/skill-index-zh.json", JSON.stringify(out, null, 1));
  console.log("SUMMARY skills=" + items.length + " failed_fallback=" + failed + " tokens_in=" + tin + " tokens_out=" + tout);
})();
