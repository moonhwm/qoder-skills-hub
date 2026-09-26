// 描述手术：对调度 miss 技能重写 frontmatter description（单行件），提升嵌入召回。
// 约束：保留原意图与触发词；覆盖 miss 触发语词表；单行 ≤600 字；平实无营销腔；YAML 安全（整行双引号包裹）。
// 引擎：plan 端点 qwen3.6-flash，并发 2。产物：直接改写 <skill>/SKILL.md + docs/desc-surgery-log.json。
const fs = require("fs");
const path = require("path");
const KEY = process.env.PLAN_KEY;
const ENDPOINT = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions";
const MODEL = "qwen3.6-flash";
const CONC = 2;

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const { ok, miss } = JSON.parse(fs.readFileSync("docs/.miss-single.json", "utf8"));

const SYS = "你是技能描述改写器。输入为旧描述与未命中触发语清单。输出一条新描述：单行、不超过600字、简体中文为主；保留旧描述的全部核心意图与专有名；把触发语中的口语词与自然并入（如触发语说'解压嵌套压缩包'则描述须出现'嵌套压缩包/解压'）；语气平实；禁止营销词；只输出新描述本身，不加引号与解释。";

async function rewrite(name, oldDesc, triggers) {
  const body = JSON.stringify({
    model: MODEL,
    temperature: 0.3,
    messages: [
      { role: "system", content: SYS },
      { role: "user", content: "旧描述：" + oldDesc + "\n未命中触发语：\n" + triggers.map((t) => "- " + t).join("\n") }
    ]
  });
  for (let a = 0; a < 2; a++) {
    try {
      const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY }, body });
      if (!r.ok) { await new Promise((s) => setTimeout(s, 2000)); continue; }
      const j = await r.json();
      const t = ((j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "").replace(/\r?\n/g, " ").trim();
      if (t.length >= 20 && t.length <= 600) return t;
    } catch (e) { await new Promise((s) => setTimeout(s, 1500)); }
  }
  return null;
}

function oldDescOf(name) {
  const t = fs.readFileSync(path.join(name, "SKILL.md"), "utf8");
  const m = t.match(/^description:\s*(.*)$/m);
  if (!m) return null;
  return m[1].trim().replace(/^"([\s\S]*)"$/, "$1");
}

(async () => {
  const log = { generatedAt: new Date().toISOString(), model: MODEL, applied: [], skipped: [] };
  let i = 0;
  async function worker() {
    while (i < ok.length) {
      const name = ok[i++];
      const oldD = oldDescOf(name);
      if (!oldD) { log.skipped.push(name + ":no-desc"); continue; }
      const neu = await rewrite(name, oldD, miss[name] || []);
      if (!neu) { log.skipped.push(name + ":gen-fail"); continue; }
      const p = path.join(name, "SKILL.md");
      let t = fs.readFileSync(p, "utf8");
      const safe = neu.replace(/"/g, "'");
      t = t.replace(/^description:\s*.*$/m, 'description: "' + safe + '"');
      fs.writeFileSync(p, Buffer.from(t, "utf8"));
      log.applied.push({ skill: name, oldLen: oldD.length, newLen: safe.length });
      console.log("applied " + log.applied.length + "/" + ok.length + " " + name);
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));
  fs.writeFileSync("docs/desc-surgery-log.json", JSON.stringify(log, null, 1));
  console.log("SUMMARY applied=" + log.applied.length + " skipped=" + log.skipped.length + (log.skipped.length ? " [" + log.skipped.join(", ") + "]" : ""));
})();
