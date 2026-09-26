// §5 证明链：claims.json 全 15 条渲染为 K1–K15 锚表，conf 分级着色，点击展开 falsifiable_test
(() => {
  const R = window.RPT; if (!R) return;
  const host = document.getElementById("claims-list");
  if (!host) return;
  const catCls = s => s === "监管平台" ? "company" : s === "官方底表" ? "industry" : "kimi";
  host.innerHTML = R.claims.map(c => `
    <div class="k-row" data-k="${c.k}">
      <div class="k-head">
        <span class="k-id">${c.k}</span>
        <span class="k-claim">${c.claim}</span>
        <span class="conf ${c.conf.toLowerCase()}">${c.conf}</span>
        <span class="k-toggle">展开证伪 ▾</span>
      </div>
      <span class="k-meta"><span class="src-cat ${catCls(c.src)}">${c.src}</span>
        核查 ${c.date}${c.url ? ` · ${c.url}` : ""}${c.noUrl ? ` · ${c.noUrl}` : ""}</span>
      <div class="k-test"><b>证伪检验 · </b>${c.test}</div>
    </div>`).join("");
  host.querySelectorAll(".k-row").forEach(row => {
    row.querySelector(".k-head").addEventListener("click", e => {
      const open = row.classList.toggle("open");
      row.querySelector(".k-toggle").textContent = open ? "收起 ▴" : "展开证伪 ▾";
      const c = window.K ? K.get(row.dataset.k) : null;
      if (open && c) { /* 展开即展示，不弹卡；双击行标题下钻 */ }
    });
    row.querySelector(".k-head").addEventListener("dblclick", e => {
      if (window.K) K.drill(row.dataset.k, e.clientX, e.clientY);
    });
  });
})();
