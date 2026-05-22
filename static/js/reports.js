(function () {
  if (!window.Chart) return;

  const daily = JSON.parse(document.getElementById("dailySeries")?.textContent || '{"labels":[],"sales":[],"profit":[]}');
  const payment = JSON.parse(document.getElementById("paymentChartData")?.textContent || '{"labels":[],"values":[]}');
  const topProducts = JSON.parse(document.getElementById("topProductChartData")?.textContent || '{"labels":[],"values":[]}');
  const categories = JSON.parse(document.getElementById("categoryChartData")?.textContent || '{"labels":[],"values":[]}');
  const palette = ["#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#0EA5E9", "#14B8A6", "#64748B"];

  function lineChart(id, label, values, color) {
    new Chart(document.getElementById(id), {
      type: "line",
      data: {
        labels: daily.labels,
        datasets: [{ label, data: values, borderColor: color, backgroundColor: `${color}22`, fill: true, tension: 0.35 }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });
  }

  function barChart(id, labels, values, label) {
    new Chart(document.getElementById(id), {
      type: "bar",
      data: { labels, datasets: [{ label, data: values, backgroundColor: palette }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });
  }

  lineChart("salesChart", "Sales", daily.sales, "#4F46E5");
  lineChart("profitChart", "Profit", daily.profit, "#10B981");

  new Chart(document.getElementById("paymentChart"), {
    type: "doughnut",
    data: { labels: payment.labels, datasets: [{ data: payment.values, backgroundColor: palette }] },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } },
  });

  barChart("topProductsChart", topProducts.labels, topProducts.values, "Top products");
  barChart("categoryChart", categories.labels, categories.values, "Category sales");
})();
