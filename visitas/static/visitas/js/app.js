/* Gráficos compartidos (Chart.js va incluido en static/). Paleta naranja y crema. */
window.FIEI = (function () {
  const PALETA = ['#d4852a', '#6b3f0d', '#3f7d5c', '#e9c58f', '#9a8f80', '#b4452f'];
  const NARANJA = '#d4852a', GRIS = '#d8cdbb', TEXTO = '#7a6650', REJILLA = '#efe2c8';
  if (window.Chart) { Chart.defaults.font.family = '"Segoe UI",system-ui,sans-serif'; }

  function ejes(titulo, horizontal) {
    const val = { beginAtZero: true, grid: { color: REJILLA }, ticks: { color: TEXTO },
                  title: { display: !!titulo, text: titulo || '', color: TEXTO } };
    const cat = { grid: { display: false }, ticks: { color: TEXTO, maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } };
    return horizontal ? { x: val, y: cat } : { x: cat, y: val };
  }

  // Escribe el valor encima de cada barra (solo si caben pocas barras)
  const etiquetas = {
    id: 'etiquetas',
    afterDatasetsDraw: function (chart, _a, op) {
      if (!op || !op.activo) return;
      const ctx = chart.ctx;
      ctx.save(); ctx.fillStyle = '#5a3a14'; ctx.font = '600 11px "Segoe UI",sans-serif';
      ctx.textAlign = 'center';
      chart.getDatasetMeta(0).data.forEach(function (barra, i) {
        const v = chart.data.datasets[0].data[i];
        ctx.fillText(Math.round(v * 10) / 10, barra.x, barra.y - 5);
      });
      ctx.restore();
    }
  };

  function barras(id, etiq, valores, op) {
    op = op || {};
    const colores = valores.map(function (_, i) { return op.grises && op.grises[i] ? GRIS : NARANJA; });
    return new Chart(document.getElementById(id), {
      type: 'bar', plugins: [etiquetas],
      data: { labels: etiq, datasets: [{ data: valores, backgroundColor: colores, borderRadius: 6, maxBarThickness: 46 }] },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, etiquetas: { activo: valores.length <= 14 } },
        scales: ejes(op.etiquetaEje) }
    });
  }

  function horizontales(id, etiq, valores, op) {
    op = op || {};
    return new Chart(document.getElementById(id), {
      type: 'bar',
      data: { labels: etiq, datasets: [{ data: valores, backgroundColor: op.color || NARANJA, borderRadius: 6, maxBarThickness: 26 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false },
          tooltip: { callbacks: { label: function (c) { return c.parsed.x + (op.sufijo || ''); } } } },
        scales: { x: Object.assign(ejes().y, { ticks: { color: TEXTO, callback: function (v) { return v + (op.sufijo || ''); } } }),
                  y: ejes().x } }
    });
  }

  function linea(id, etiq, valores, op) {
    op = op || {};
    const cv = document.getElementById(id), g = cv.getContext('2d');
    const rel = g.createLinearGradient(0, 0, 0, cv.parentNode.clientHeight || 300);
    rel.addColorStop(0, 'rgba(212,133,42,.38)'); rel.addColorStop(1, 'rgba(212,133,42,0)');
    return new Chart(cv, {
      type: 'line',
      data: { labels: etiq, datasets: [{ data: valores, borderColor: NARANJA, backgroundColor: rel, fill: true,
        borderWidth: 2, pointRadius: valores.length <= 40 ? 3 : 0, pointHoverRadius: 5, tension: 0.3 }] },
      options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
        plugins: { legend: { display: false } }, scales: ejes(op.etiquetaEje) }
    });
  }

  function dona(id, etiq, valores) {
    return new Chart(document.getElementById(id), {
      type: 'doughnut',
      data: { labels: etiq, datasets: [{ data: valores, backgroundColor: PALETA, borderColor: '#fffdf9', borderWidth: 3 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: '64%',
        plugins: { legend: { position: 'right', labels: { color: TEXTO, boxWidth: 12, usePointStyle: true } } } }
    });
  }

  return { barras: barras, horizontales: horizontales, linea: linea, dona: dona, PALETA: PALETA, NARANJA: NARANJA, TEXTO: TEXTO, REJILLA: REJILLA };
})();
