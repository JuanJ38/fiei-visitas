/* Funciones de gráficos compartidas (usan Chart.js, que va incluido en static/). */
window.FIEI = (function () {
  const AZUL = '#1d4f91';
  const GRIS = '#a8b3c4';
  const TEXTO = '#475569';
  const REJILLA = '#e2e8f0';

  function ejes(etiquetaEje) {
    return {
      x: { grid: { display: false }, ticks: { color: TEXTO, maxRotation: 60, autoSkip: true } },
      y: {
        beginAtZero: true,
        grid: { color: REJILLA },
        ticks: { color: TEXTO },
        title: { display: !!etiquetaEje, text: etiquetaEje || '', color: TEXTO }
      }
    };
  }

  function barras(id, etiquetas, valores, op) {
    op = op || {};
    const colores = valores.map(function (_, i) {
      return op.grises && op.grises[i] ? GRIS : AZUL;
    });
    return new Chart(document.getElementById(id), {
      type: 'bar',
      data: { labels: etiquetas, datasets: [{ data: valores, backgroundColor: colores, borderRadius: 4 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: ejes(op.etiquetaEje)
      }
    });
  }

  function linea(id, etiquetas, valores, op) {
    op = op || {};
    return new Chart(document.getElementById(id), {
      type: 'line',
      data: {
        labels: etiquetas,
        datasets: [{
          data: valores, borderColor: AZUL, backgroundColor: 'rgba(29,79,145,.10)',
          fill: true, borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 4, tension: 0.15
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { display: false } },
        scales: ejes(op.etiquetaEje)
      }
    });
  }

  return { barras: barras, linea: linea };
})();
