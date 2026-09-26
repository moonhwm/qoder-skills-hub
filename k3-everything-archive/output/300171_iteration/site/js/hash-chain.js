// §7 哈希链：18 节点全表（SHA-256 截断显示、点击展开全值；创世节点与根节点标注）
(() => {
  const R = window.RPT; if (!R) return;
  const host = document.getElementById("hash-table");
  if (!host) return;
  const HC = R.hashChain;
  const tr = h => h.slice(0, 10) + "…" + h.slice(-6);
  host.innerHTML = `
    <p class="chart-title">哈希链登记 · ${HC.nodes.length} 节点</p>
    <p class="chart-sub">SHA-256 截断显示 · 点击哈希展开全值 · CHAIN_NODE = SHA256(文件哈希 + 前驱节点) · 生成 ${HC.generatedAt}</p>
    <table class="dt hash"><thead><tr>
      <th>#</th><th>文件</th><th>SHA-256</th><th>链式节点</th><th>前驱</th></tr></thead>
      <tbody>${HC.nodes.map((n, i) => {
        const genesis = n.prev.startsWith("0000");
        const isRoot = n.node === HC.root;
        return `<tr${isRoot ? ' class="hl"' : ""}>
        <td class="num">${String(i + 1).padStart(2, "0")}</td>
        <td>${n.file}${genesis ? ' <span class="conf method">创世</span>' : ""}${isRoot ? ' <span class="conf high">ROOT</span>' : ""}</td>
        <td class="mono hx" data-full="${n.sha}">${tr(n.sha)}</td>
        <td class="mono hx" data-full="${n.node}">${tr(n.node)}</td>
        <td class="mono hx" data-full="${n.prev}">${genesis ? "00…00" : tr(n.prev)}</td>
      </tr>`; }).join("")}</tbody></table>
    <p class="chart-src">Source · data/hash_chain.json（${HC.generatedAt}）· root ${tr(HC.root)}</p>`;
  host.querySelectorAll(".hx").forEach(td => {
    td.addEventListener("click", () => {
      const open = td.classList.toggle("open");
      td.textContent = open ? td.dataset.full
        : (td.dataset.full.startsWith("0000") ? "00…00" : td.dataset.full.slice(0, 10) + "…" + td.dataset.full.slice(-6));
    });
  });
})();
