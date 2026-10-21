let velocityChartInstance = null;
let categoryChartInstance = null;
let supplierChartInstance = null;

function renderVelocityDonut(distributionData) {
  const canvas = document.getElementById('velocityDonutChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (velocityChartInstance) {
    velocityChartInstance.destroy();
  }

  const counts = [
    distributionData.fast.count,
    distributionData.medium.count,
    distributionData.slow.count,
    distributionData.dead.count
  ];

  const values = [
    distributionData.fast.inventory_value,
    distributionData.medium.inventory_value,
    distributionData.slow.inventory_value,
    distributionData.dead.inventory_value
  ];

  velocityChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Fast Moving (≤45d)', 'Medium (46-90d)', 'Slow (91-180d)', 'Dead Stock (>180d)'],
      datasets: [{
        data: counts,
        backgroundColor: ['#059669', '#d97706', '#ea580c', '#dc2626'],
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: { family: 'Inter', size: 11, weight: '500' },
            padding: 12
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const idx = context.dataIndex;
              const count = counts[idx];
              const val = values[idx].toLocaleString();
              return ` ${context.label}: ${count} SKUs (৳${val} Value)`;
            }
          }
        }
      },
      cutout: '72%'
    }
  });
}

function renderCategoryBarChart(categoryData) {
  const canvas = document.getElementById('categoryBarChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const topCats = categoryData.slice(0, 7);
  const labels = topCats.map(c => c.category.length > 20 ? c.category.substring(0, 18) + '...' : c.category);
  const cogsData = topCats.map(c => c.cogs);

  categoryChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'COGS Volume (৳)',
        data: cogsData,
        backgroundColor: '#1e3a8a',
        borderRadius: 4,
        maxBarThickness: 24
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` COGS: ৳${context.raw.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { family: 'Inter', size: 10 },
            callback: function(value) {
              return '৳' + (value >= 1000 ? (value / 1000).toFixed(0) + 'k' : value);
            }
          }
        },
        y: {
          grid: { display: false },
          ticks: { font: { family: 'Inter', size: 10, weight: '500' } }
        }
      }
    }
  });
}

function renderSupplierBarChart(supplierData) {
  const canvas = document.getElementById('supplierPerformanceChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (supplierChartInstance) {
    supplierChartInstance.destroy();
  }

  const topSuppliers = supplierData.slice(0, 8);
  const labels = topSuppliers.map(s => s.supplier_name.length > 18 ? s.supplier_name.substring(0, 16) + '...' : s.supplier_name);
  const cogsData = topSuppliers.map(s => s.cogs);

  supplierChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Supplier COGS (৳)',
        data: cogsData,
        backgroundColor: '#2563eb',
        borderRadius: 4,
        maxBarThickness: 24
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` Sales COGS: ৳${context.raw.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Inter', size: 10 } }
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { family: 'Inter', size: 10 },
            callback: function(value) {
              return '৳' + (value >= 1000 ? (value / 1000).toFixed(0) + 'k' : value);
            }
          }
        }
      }
    }
  });
}

let forecastChartInstance = null;

function renderForecastTrajectoryChart(fcData) {
  const canvas = document.getElementById('forecastTrajectoryChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  const histLabels = fcData.history_labels || [];
  const histSales = fcData.history_sales || [];
  const futLabels = fcData.future_labels || [];
  const p10 = fcData.p10_forecast || [];
  const p50 = fcData.p50_forecast || [];
  const p90 = fcData.p90_forecast || [];

  const combinedLabels = [...histLabels, ...futLabels];

  // Align datasets across continuous x-axis
  const histPadded = [...histSales, ...new Array(futLabels.length).fill(null)];

  // Future datasets connect at the last historical point
  const lastHistVal = histSales.length > 0 ? histSales[histSales.length - 1] : 0;
  const leadPadding = new Array(Math.max(0, histLabels.length - 1)).fill(null);

  const p50Padded = [...leadPadding, lastHistVal, ...p50];
  const p90Padded = [...leadPadding, lastHistVal, ...p90];
  const p10Padded = [...leadPadding, lastHistVal, ...p10];

  forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: combinedLabels,
      datasets: [
        {
          label: 'Historical Weekly Sales',
          data: histPadded,
          borderColor: '#1e3a8a',
          backgroundColor: '#1e3a8a',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.1,
          fill: false
        },
        {
          label: 'AI Forecast (p50 Median)',
          data: p50Padded,
          borderColor: '#059669',
          borderWidth: 2.5,
          borderDash: [5, 5],
          pointRadius: 4,
          pointBackgroundColor: '#059669',
          tension: 0.2,
          fill: false
        },
        {
          label: 'Upper Buffer (p90 Surge)',
          data: p90Padded,
          borderColor: 'rgba(5, 150, 105, 0.25)',
          borderWidth: 1,
          pointRadius: 0,
          fill: '+1',
          backgroundColor: 'rgba(5, 150, 105, 0.10)',
          tension: 0.2
        },
        {
          label: 'Lower Bound (p10)',
          data: p10Padded,
          borderColor: 'rgba(5, 150, 105, 0.25)',
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            boxWidth: 12,
            font: { family: 'Inter', size: 11, weight: '500' }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw;
              if (val === null || val === undefined) return '';
              return ` ${context.dataset.label}: ${val} pcs`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Inter', size: 10 },
            maxRotation: 45,
            autoSkip: true,
            maxTicksLimit: 14
          }
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { family: 'Inter', size: 10 },
            callback: function(value) { return value + ' pcs'; }
          },
          beginAtZero: true
        }
      }
    }
  });
}
