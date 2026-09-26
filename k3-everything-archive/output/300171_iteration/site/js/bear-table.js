// §3 空头检验台：命题判定表（确认/证伪/部分证伪分级着色，行点击下钻 K 锚）
(() => {
  const R = window.RPT; if (!R || !window.U) return;
  const host = document.getElementById("bear-table");
  if (!host) return;
  const body = U.frame(host, {
    title: "命题判定：两条确认置顶，质押减持被证伪",
    sub: "判定=确认 / 证伪 / 部分证伪 / 弱风险 / 存疑待证 · CONF 分级着色 · 点击行展开证据与证伪方法",
    src: "报告 §四 扰动测试结果（2026-08-28）· K4–K9 / K13",
  });
  const wrap = document.createElement("div");
  body.appendChild(wrap);
  const VTXT = { confirmed: "确认", falsified: "证伪", partial: "部分证伪", weak: "弱风险", pending: "存疑待证" };
  wrap.innerHTML = `<table class="dt"><thead><tr>
    <th>命题</th><th>判定</th><th>证据摘要</th><th>CONF</th><th>锚</th></tr></thead>
    <tbody>${R.bearBench.map((b, i) => `
      <tr data-i="${i}" style="cursor:pointer"${b.verdict === "confirmed" ? ' class="hl"' : ""}>
        <td><b>${b.id}</b> ${b.prop}</td>
        <td><span class="v-badge ${b.verdict}">${VTXT[b.verdict] || b.result}</span></td>
        <td style="font-size:12.5px;color:var(--ink-md)">${b.evidence}</td>
        <td><span class="conf ${b.conf.toLowerCase().split("/")[0]}">${b.conf}</span></td>
        <td><button class="klink" data-k="${b.k}" data-drill-keep>${b.k}</button></td>
      </tr>`).join("")}</tbody></table>`;
  wrap.querySelectorAll("tr[data-i]").forEach(tr => {
    tr.addEventListener("click", e => {
      if (e.target.closest(".klink")) return;
      const b = R.bearBench[+tr.dataset.i];
      const c = window.K ? K.get(b.k) : null;
      U.showDrill({
        title: `${b.id} ${b.prop} · ${b.result}`,
        value: VTXT[b.verdict] || b.result,
        sub: `${b.evidence}。来源：${b.src}${c ? "。证伪检验：" + c.test : ""}`,
        source: c ? K.srcLine(c) : `报告 §四 · 2026-08-28 · conf=${b.conf}`,
        x: e.clientX, y: e.clientY,
      });
    });
  });
})();
