// SHA3-256 梅克尔完整性树。
// gen：对 git 跟踪文件逐文件取 SHA3-256 叶子，按路径排序两两拼接哈希至根，写 MERKle.json。
// verify：重算并比对；一致退出 0，不一致列出差异文件退出 1。
// 哈希族校验不依赖公钥密码学，作为后量子完整性基线（SHA-3，NIST FIPS 202）。
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");

const mode = process.argv[2] === "gen" ? "gen" : "verify";
const h = (buf) => crypto.createHash("sha3-256").update(buf).digest();

let files = execSync("git ls-files -z").toString().split("\0").filter(Boolean);
files = files.filter((f) => f !== "MERKLE.json" && fs.existsSync(f)).sort();

const leaves = files.map((f) => ({ f, hash: h(fs.readFileSync(f)) }));

function rootOf(leafHashes) {
  let level = leafHashes.slice();
  while (level.length > 1) {
    const next = [];
    for (let i = 0; i < level.length; i += 2) {
      const l = level[i];
      const r = i + 1 < level.length ? level[i + 1] : level[i];
      next.push(h(Buffer.concat([l, r])));
    }
    level = next;
  }
  return level[0] || h(Buffer.alloc(0));
}

const root = rootOf(leaves.map((l) => l.hash));
const rootHex = root.toString("hex");

if (mode === "gen") {
  const obj = {
    algorithm: "SHA3-256 (FIPS 202), merkle binary tree, leaves sorted by path",
    generatedAt: new Date().toISOString(),
    fileCount: files.length,
    root: rootHex,
    files: {}
  };
  for (const l of leaves) obj.files[l.f] = l.hash.toString("hex");
  fs.writeFileSync("MERKLE.json", JSON.stringify(obj, null, 1));
  console.log("gen ok root=" + rootHex + " files=" + files.length);
} else {
  if (!fs.existsSync("MERKLE.json")) { console.log("verify fail: MERKLE.json 不存在"); process.exit(1); }
  const m = JSON.parse(fs.readFileSync("MERKLE.json", "utf8"));
  const bad = [];
  for (const l of leaves) {
    if ((m.files || {})[l.f] !== l.hash.toString("hex")) bad.push(l.f);
  }
  for (const f of Object.keys(m.files || {})) {
    if (!files.includes(f)) bad.push(f + " (manifest 有而工作区无)");
  }
  if (m.root !== rootHex) bad.push("(root 不一致: manifest=" + m.root + " 实算=" + rootHex + ")");
  if (bad.length) {
    console.log("verify fail diff=" + bad.length);
    bad.slice(0, 30).forEach((x) => console.log("  " + x));
    process.exit(1);
  }
  console.log("verify ok root=" + rootHex + " files=" + files.length);
}
