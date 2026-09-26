// 评测集生成批：为每件技能生成 3 条调度评测用例（触发语/期望行为/判定关键词）。
// 引擎：百炼 TokenPlan 专属端点 qwen3.6-flash，并发 2。
// 产物：docs/evals/<skill>.json；汇总 docs/evals-index.json。
// 用途：技能调度自检——用触发语回查是否命中本件（dispatch 回归基线）。
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const KEY = process.env.PLAN_KEY;
const ENDPOINT = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions";
const MODEL = "qwen3.6-flash";
const CONC = 2;
const PROG = ".evals-progress.json";

const idx = JSON.parse(fs.readFileSync("docs/skill-index-zh.json", "utf8")).entries;
const names = Object.keys(idx).sort();
const progress = fs.existsSync(PROG) ? JSON.parse(fs.readFileSync(PROG, "utf8")) : { done: {}, stats: { cases: 0, fallback: 0, tin: 0, tout: 0 } };

const SYS = "你是技能调度评测设计器。输入为技能名、中文摘要与关键词。输出严格 JSON：{\"cases\":[3 条对象，每条 {\"trigger\":\"一句真实用户口吻的触发语（简体中文，口语化）\",\"expect\":\"期望的技能行为一句话\",\"judge\":[2至4个判定关键词]}]}。只输出 JSON。";

async function gen(name) {
  const e = idx[name];
  const body = JSON.stringify({
    model: MODEL,
    temperature: 0.4,
    messages: [
      { role: "system", content: SYS },
      { role: "user", content: "name: " + name + "\nsummary: " + (e.summary_zh || "") + "\nkeywords: " + (e.keywords || []).join("、") }
    ]
  });
  for (let a = 0; a < 2; a++) {
    try {
      const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY }, body });
      if (!r.ok) { if (r.status === 429) await new Promise((s) => setTimeout(s, 3000)); continue; }
      const j = await r.json();
      progress.stats.tin += (j.usage && j.usage.prompt_tokens) || 0;
      progress.stats.tout += (j.usage && j.usage.completion_tokens) || 0;
      const t = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
      const mm = t.match(/\{[\s\S]*\}/);
      if (!mm) continue;
      const o = JSON.parse(mm[0]);
      if (Array.isArray(o.cases) && o.cases.length === 3 && o.cases.every((c) => c.trigger && c.expect && Array.isArray(c.judge))) return o.cases;
    } catch (e2) { await new Promise((s) => setTimeout(s, 1500)); }
  }
  return null;
}

(async () => {
  fs.mkdirSync("docs/evals", { recursive: true });
  const todo = names.filter((n) => !progress.done[n]);
  let i = 0;
  async function worker() {
    while (i < todo.length) {
      const n = todo[i++];
      const cases = await gen(n);
      if (cases) {
        fs.writeFileSync("docs/evals/" + n + ".json", JSON.stringify({ skill: n, generatedAt: new Date().toISOString(), cases }, null, 1));
        progress.stats.cases += cases.length;
      } else {
        progress.stats.fallback++;
        fs.writeFileSync("docs/evals/" + n + ".json", JSON.stringify({ skill: n, generatedAt: new Date().toISOString(), cases: [{ trigger: "请使用 " + n, expect: idx[n].summary_zh || "", judge: (idx[n].keywords || []).slice(0, 3) }] }, null, 1));
      }
      progress.done[n] = 1;
      if (i % 10 === 0) { fs.writeFileSync(PROG, JSON.stringify(progress)); console.log("progress " + i + "/" + todo.length); }
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));
  fs.writeFileSync(PROG, JSON.stringify(progress));
  const summary = { generatedAt: new Date().toISOString(), skills: names.length, fallback: progress.stats.fallback, tokens: { in: progress.stats.tin, out: progress.stats.tout } };
  fs.writeFileSync("docs/evals-index.json", JSON.stringify(summary, null, 1));
  console.log("SUMMARY skills=" + todo.length + " cases=" + progress.stats.cases + " fallback=" + progress.stats.fallback + " tin=" + progress.stats.tin + " tout=" + progress.stats.tout);
})();
