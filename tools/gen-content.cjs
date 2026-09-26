// 多平台可发布内容包生成：主题＝OpenPlanLink 幻16 桥接节点（单总线 A2A 叙事）。
// 引擎：百炼赠送额度 key，qwen3.7-max（高价值燃烧）。产物：docs/content-pack/*.md。
// 平台：微信公众号 / 小红书 / 知乎 / 哔哩哔哩专栏。去 AI 腔要求写入系统提示。
const fs = require("fs");
const path = require("path");
const KEY = process.env.GIFT_KEY;
const ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions";
const MODEL = process.env.CONTENT_MODEL || "qwen3.8-omni-flash";

const ROOT = process.argv[2] || ".";
process.chdir(ROOT);
const cover = fs.existsSync("../runtime/cover-text.txt") ? fs.readFileSync("../runtime/cover-text.txt", "utf8") : "";
const facts = [
  "OpenPlanLink 幻16 桥接节点：一台 2022 笔记本上长出的 A2A（Agent2Agent）桥接节点，把私有消息总线变为开放、符合规范的 agent 网络。",
  "公开发现面：/.well-known/agent-card.json 动态卡、/llms.txt 预载面、SHA3-256 梅克尔树完整性基线（后量子哈希族）。",
  "安全：进程内防火墙限流 + 双因子（席位密钥 + RFC-6238 TOTP）门禁特权方法；公开互操作面保持无凭据。",
  "技能库：github.com/moonhwm/qoder-skills-hub，91 件技能、简体中文 README、273 条调度评测、57 边交叉引用图。",
  "连通计划：云端（Qoder Cloud Agents + 百炼额度）× 本地（watchdog + serveo 隧道）× peer（DeepSeek harness / hermess / EvoMap）单总线握手；WorkBuddy 席位为初始化点。",
  "研究约束：跨境单总线只动引用不动原始数据；境内段按大型局域网治理；拓扑分层可演进。",
  cover ? "节点封面语气样本：" + cover.slice(0, 400) : ""
].filter(Boolean).join("\n");

const PLATFORMS = {
  wechat: "微信公众号长文：标题+导语+三到四节正文+结尾互动问句；1200至1600字；克制抒情，多事实与数字；小标题用中文序号。",
  xhs: "小红书笔记：首行钩子标题（≤20字）+正文 300至450 字 + 5至8 个话题标签；口语但信息密度高；可用少量 emoji（≤3）。",
  zhihu: "知乎回答体：先给结论段，再分点论证，含一处反常识观察与一处自我局限声明；900至1300字。",
  bili: "哔哩哔哩专栏：技术叙事+个人历程双线；800至1200字；结尾留一个开放问题给弹幕/评论。"
};
const SYS = "你是中文技术写作者。把给定事实改写为指定平台稿件。要求：平实、具体、有数字与名词锚点；禁止营销腔、禁止空泛形容词堆砌、禁止'赋能/助力/一站式/打造'等词；事实不得超出给定材料，不足处明说'暂未公开'。只输出稿件正文。";

async function gen(platform, spec) {
  const body = JSON.stringify({
    model: MODEL,
    temperature: 0.7,
    messages: [
      { role: "system", content: SYS },
      { role: "user", content: "平台规格：" + spec + "\n\n事实材料：\n" + facts }
    ]
  });
  for (let a = 0; a < 3; a++) {
    try {
      const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY }, body });
      if (!r.ok) { await new Promise((s) => setTimeout(s, 2500)); continue; }
      const j = await r.json();
      const t = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
      if (t.length > 80) return { text: t, usage: j.usage || {} };
    } catch (e) { await new Promise((s) => setTimeout(s, 2000)); }
  }
  return null;
}

(async () => {
  fs.mkdirSync("docs/content-pack", { recursive: true });
  const ledger = { generatedAt: new Date().toISOString(), model: MODEL, usage: {}, ok: [], failed: [] };
  for (const [p, spec] of Object.entries(PLATFORMS)) {
    const r = await gen(p, spec);
    if (r) {
      fs.writeFileSync("docs/content-pack/" + p + ".md", "# " + p + " 稿（2026-09-27 生成，待人工审后发布）\n\n" + r.text + "\n");
      ledger.ok.push(p);
      ledger.usage[p] = r.usage;
    } else ledger.failed.push(p);
    console.log("platform " + p + " " + (r ? "ok chars=" + r.text.length : "FAILED"));
  }
  fs.writeFileSync("docs/content-pack/ledger.json", JSON.stringify(ledger, null, 1));
  console.log("SUMMARY ok=" + ledger.ok.join(",") + " failed=" + (ledger.failed.join(",") || "none"));
})();
