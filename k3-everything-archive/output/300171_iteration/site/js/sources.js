// K 锚下钻助手：站内所有关键数字 → U.showDrill 到对应 K 锚
window.K = (() => {
  const byId = {};
  (window.RPT && window.RPT.claims || []).forEach(c => { byId[c.k] = c; });
  function get(k) { return byId[k] || null; }
  function srcLine(c) {
    const base = `${c.src} · 核查 ${c.date} · conf=${c.conf}`;
    return base + (c.url ? ` · ${c.url}` : (c.noUrl ? ` · ${c.noUrl}` : ""));
  }
  function drill(k, x, y) {
    const c = get(k);
    if (!c) return;
    U.showDrill({
      title: `${k} · 证据锚 · CONF=${c.conf.toUpperCase()}`,
      value: c.claim.length > 64 ? c.claim.slice(0, 64) + "…" : c.claim,
      sub: `证伪检验：${c.test}`,
      source: srcLine(c), x, y,
    });
  }
  return { get, drill, srcLine };
})();
