// Intelligent Expense Tracker - Chart.js Initializers v3.0

const FINTECH_PALETTE = [
  '#2563eb', // Royal Blue
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#f97316', // Orange
  '#64748b', // Slate
  '#14b8a6', // Teal
  '#6366f1'  // Indigo
];

function initMonthlyTrendChart(canvasId, trendData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !trendData) return null;

  const labels = trendData.map(d => d.month);
  const incomeValues = trendData.map(d => d.income);
  const expenseValues = trendData.map(d => d.expense);

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Current Cycle'],
      datasets: [
        {
          label: 'Income (₹)',
          data: incomeValues.length ? incomeValues : [0],
          backgroundColor: '#10b981',
          borderRadius: 8,
          barPercentage: 0.55,
          categoryPercentage: 0.65
        },
        {
          label: 'Expense (₹)',
          data: expenseValues.length ? expenseValues : [0],
          backgroundColor: '#3b82f6',
          borderRadius: 8,
          barPercentage: 0.55,
          categoryPercentage: 0.65
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 800,
        easing: 'easeOutQuart'
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { size: 12, weight: '600', family: "'Plus Jakarta Sans', sans-serif" },
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          padding: 12,
          cornerRadius: 8,
          titleFont: { size: 12, weight: '700', family: "'Plus Jakarta Sans', sans-serif" },
          bodyFont: { size: 13, weight: '600', family: "'JetBrains Mono', monospace" },
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) label += ': ';
              label += '₹' + Number(context.raw).toLocaleString('en-IN', { minimumFractionDigits: 2 });
              return label;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 11, weight: '600', family: "'Plus Jakarta Sans', sans-serif" },
            color: '#64748b'
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(241, 245, 249, 0.9)' },
          ticks: {
            font: { size: 11, family: "'JetBrains Mono', monospace" },
            color: '#94a3b8',
            callback: function(value) {
              return '₹' + Number(value).toLocaleString('en-IN');
            }
          }
        }
      }
    }
  });
}

function initCategoryDoughnutChart(canvasId, categoryData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const hasData = categoryData && categoryData.length > 0;
  const labels = hasData ? categoryData.map(c => c.category) : ['No Outflows'];
  const values = hasData ? categoryData.map(c => c.total) : [1];
  const bgColors = hasData ? FINTECH_PALETTE.slice(0, categoryData.length) : ['#e2e8f0'];

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: bgColors,
        borderWidth: 3,
        borderColor: '#ffffff',
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      animation: {
        animateRotate: true,
        duration: 900
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 8,
            boxHeight: 8,
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 14,
            font: { size: 11, weight: '600', family: "'Plus Jakarta Sans', sans-serif" },
            color: '#475569'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          padding: 12,
          cornerRadius: 8,
          enabled: hasData,
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}
