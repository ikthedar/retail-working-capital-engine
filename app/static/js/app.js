// State Management
const state = {
  horizon: '1m',
  asOfDate: '2026-10-19',
  productSortMode: 'units',     // 'units' or 'cogs'
  supplierSortMode: 'units',    // 'units' or 'cogs'
  tablePage: 1,
  tablePageSize: 25,
  tableSearch: '',
  tableCategory: 'All',
  tableSupplier: 'All',
  tableVelocity: 'All',
  tableSortBy: 'cogs',
  tableSortOrder: 'desc'
};

// Formatting Utilities
function formatCurrency(val) {
  if (val === null || val === undefined) return '৳0';
  return '৳' + Number(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatNumber(val) {
  if (val === null || val === undefined) return '0';
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

function showToast(msg) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>✓</span> <span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// API Calls
async function fetchKPIs() {
  try {
    const res = await fetch(`/api/analytics/kpi-summary?horizon=${state.horizon}&as_of=${state.asOfDate}`);
    const data = await res.json();
    
    document.getElementById('kpiTotalValue').textContent = formatCurrency(data.total_inventory_value);
    document.getElementById('kpiTotalUnits').textContent = formatNumber(data.total_stock_units) + ' pcs';
    document.getElementById('kpiActiveSKUs').textContent = `${data.active_moving_products_count} / ${data.total_products_count}`;
    document.getElementById('kpiPeriodCOGS').textContent = formatCurrency(data.period_cogs);
    document.getElementById('kpiPeriodUnits').textContent = `${formatNumber(data.period_units_sold)} pcs sold`;
    document.getElementById('kpiTurnoverRatio').textContent = `${data.overall_annualized_turnover.toFixed(2)}x`;
    document.getElementById('kpiTurnoverSubtitle').textContent = `Period: ${data.overall_turnover_ratio.toFixed(2)}x`;
    document.getElementById('kpiAverageDSI').textContent = data.average_dsi ? `${Math.round(data.average_dsi)} days` : 'N/A';
  } catch (err) {
    console.error('Error fetching KPIs:', err);
  }
}

async function fetchTopProducts() {
  const listEl = document.getElementById('topProductsList');
  listEl.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">Loading top products...</div>';

  try {
    const res = await fetch(`/api/analytics/top-products?horizon=${state.horizon}&as_of=${state.asOfDate}&sort_by=${state.productSortMode}&limit=10`);
    const data = await res.json();

    if (!data || data.length === 0) {
      listEl.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">No sales recorded in this period.</div>';
      return;
    }

    listEl.innerHTML = '';
    data.forEach(item => {
      const primaryMetric = state.productSortMode === 'units'
        ? `${formatNumber(item.units_sold)} pcs`
        : formatCurrency(item.cogs);
      
      const secondaryMetric = state.productSortMode === 'units'
        ? `COGS: ${formatCurrency(item.cogs)}`
        : `Volume: ${formatNumber(item.units_sold)} pcs`;

      const el = document.createElement('div');
      el.className = 'leaderboard-item';
      el.onclick = () => openProductLedgerModal(item.id);
      el.innerHTML = `
        <div class="leaderboard-rank rank-${item.rank <= 3 ? item.rank : 'default'}">${item.rank}</div>
        <div class="leaderboard-details">
          <div class="leaderboard-title">${item.product_name}</div>
          <div class="leaderboard-meta">
            <span>🏷️ ${item.category}</span>
            <span>📦 Stock: ${item.current_stock} pcs</span>
            <span>⏳ Run-out: ${item.run_out_days !== null ? Math.round(item.run_out_days) + 'd' : '∞'}</span>
          </div>
        </div>
        <div class="leaderboard-metrics">
          <div class="metric-primary">${primaryMetric}</div>
          <div class="metric-secondary">${secondaryMetric}</div>
        </div>
      `;
      listEl.appendChild(el);
    });
  } catch (err) {
    console.error('Error fetching top products:', err);
  }
}

async function fetchTopSuppliers() {
  const listEl = document.getElementById('topSuppliersList');
  if (!listEl) return;
  listEl.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">Loading supplier sales...</div>';

  try {
    const res = await fetch(`/api/analytics/top-suppliers?horizon=${state.horizon}&as_of=${state.asOfDate}&sort_by=${state.supplierSortMode}&limit=10`);
    const data = await res.json();

    if (!data || data.length === 0) {
      listEl.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">No supplier sales found in this period.</div>';
      return;
    }

    listEl.innerHTML = '';
    data.forEach(item => {
      const primaryMetric = state.supplierSortMode === 'units'
        ? `${formatNumber(item.units_sold)} pcs`
        : formatCurrency(item.cogs);

      const secondaryMetric = state.supplierSortMode === 'units'
        ? `COGS: ${formatCurrency(item.cogs)}`
        : `Volume: ${formatNumber(item.units_sold)} pcs`;

      const el = document.createElement('div');
      el.className = 'leaderboard-item clickable-supplier';
      el.title = `Click to inspect ${item.supplier_name}'s sold products & inventory valuation`;
      el.onclick = () => openSupplierDetailModal(item.supplier_name);
      el.innerHTML = `
        <div class="leaderboard-rank rank-${item.rank <= 3 ? item.rank : 'default'}">${item.rank}</div>
        <div class="leaderboard-details">
          <div class="leaderboard-title" style="display: flex; align-items: center; justify-content: space-between; padding-right: 0.5rem;">
            <span>${item.supplier_name}</span>
            <span style="font-size: 0.72rem; color: #2563eb; background: #eff6ff; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 600;">🔍 Inspect</span>
          </div>
          <div class="leaderboard-meta">
            <span>📦 Active Stock: ${formatNumber(item.current_stock)} pcs</span>
            <span>💼 Value Held: ${formatCurrency(item.total_inventory_value)}</span>
            <span>📊 Turnover: ${item.turnover_ratio}x</span>
          </div>
        </div>
        <div class="leaderboard-metrics">
          <div class="metric-primary">${primaryMetric}</div>
          <div class="metric-secondary">${secondaryMetric}</div>
        </div>
      `;
      listEl.appendChild(el);
    });

    renderSupplierBarChart(data);
  } catch (err) {
    console.error('Error fetching top suppliers:', err);
  }
}

async function fetchVisualCharts() {
  try {
    const [vRes, cRes] = await Promise.all([
      fetch(`/api/analytics/velocity-distribution?horizon=${state.horizon}&as_of=${state.asOfDate}`),
      fetch(`/api/analytics/category-performance?horizon=${state.horizon}&as_of=${state.asOfDate}`)
    ]);
    const vData = await vRes.json();
    const cData = await cRes.json();

    renderVelocityDonut(vData);
    renderCategoryBarChart(cData);
  } catch (err) {
    console.error('Error fetching chart data:', err);
  }
}

async function fetchProductTable() {
  const tbody = document.getElementById('productTableBody');
  tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading inventory catalog...</td></tr>';

  try {
    const params = new URLSearchParams({
      page: state.tablePage,
      page_size: state.tablePageSize,
      horizon: state.horizon,
      as_of: state.asOfDate,
      sort_by: state.tableSortBy,
      sort_order: state.tableSortOrder
    });

    if (state.tableSearch) params.append('search', state.tableSearch);
    if (state.tableCategory && state.tableCategory !== 'All') params.append('category', state.tableCategory);
    if (state.tableSupplier && state.tableSupplier !== 'All') params.append('supplier', state.tableSupplier);
    if (state.tableVelocity && state.tableVelocity !== 'All') params.append('velocity', state.tableVelocity);

    const res = await fetch(`/api/inventory/products?${params.toString()}`);
    const data = await res.json();

    tbody.innerHTML = '';
    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 2rem; color: var(--text-muted);">No products match the selected filters.</td></tr>';
      document.getElementById('paginationInfo').textContent = 'Showing 0 of 0 products';
      return;
    }

    data.items.forEach(p => {
      const tr = document.createElement('tr');
      tr.onclick = () => openProductLedgerModal(p.id);

      const tierClass = `badge-${p.velocity_tier}`;
      const tierLabel = p.velocity_tier.toUpperCase();

      tr.innerHTML = `
        <td><strong>${p.product_name}</strong><br><small style="color: var(--text-muted);">${p.sub_type || p.tool_type || ''}</small></td>
        <td>${p.category}</td>
        <td>${p.supplier_name || '—'}</td>
        <td style="text-align: right;">${formatCurrency(p.unit_cost)}</td>
        <td style="text-align: right;">${p.current_stock}</td>
        <td style="text-align: right;">${formatCurrency(p.total_value)}</td>
        <td style="text-align: right; font-weight: 600;">${formatNumber(p.units_sold)}</td>
        <td style="text-align: right; color: var(--navy-primary); font-weight: 700;">${formatCurrency(p.cogs)}</td>
        <td style="text-align: right;">${p.turnover_ratio}x</td>
        <td><span class="badge-tier ${tierClass}">${tierLabel}</span></td>
      `;
      tbody.appendChild(tr);
    });

    const startItem = (data.page - 1) * data.page_size + 1;
    const endItem = Math.min(data.page * data.page_size, data.total);
    document.getElementById('paginationInfo').textContent = `Showing ${startItem}–${endItem} of ${data.total} products`;

    document.getElementById('prevPageBtn').disabled = (data.page <= 1);
    document.getElementById('nextPageBtn').disabled = (data.page >= data.total_pages);
  } catch (err) {
    console.error('Error fetching table data:', err);
  }
}

async function openProductLedgerModal(productId) {
  const modal = document.getElementById('ledgerModal');
  const modalBody = document.getElementById('ledgerModalBody');
  const modalTitle = document.getElementById('ledgerModalTitle');

  modal.classList.add('open');
  modalBody.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading transaction history...</div>';

  try {
    const res = await fetch(`/api/inventory/products/${productId}`);
    const data = await res.json();

    modalTitle.textContent = data.product_name;

    let txRows = '';
    if (data.transactions && data.transactions.length > 0) {
      data.transactions.forEach(t => {
        const typeClass = t.type === 'SALE' ? 'type-badge-sale' : (t.type === 'PURCHASE' ? 'type-badge-purchase' : 'type-badge-shrinkage');
        txRows += `
          <tr>
            <td>${t.date}</td>
            <td class="${typeClass}">${t.type}</td>
            <td style="text-align: right;">${t.quantity} ${t.unit}</td>
            <td style="text-align: right;">${formatCurrency(t.unit_cost)}</td>
            <td style="text-align: right; font-weight: 600;">${formatCurrency(t.total_value)}</td>
            <td style="color: var(--text-secondary); font-size: 0.75rem;">${t.raw_text}</td>
          </tr>
        `;
      });
    } else {
      txRows = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No transaction entries found for this product.</td></tr>';
    }

    modalBody.innerHTML = `
      <div class="modal-product-summary">
        <div>
          <div class="summary-stat-label">Category</div>
          <div class="summary-stat-value" style="font-size: 0.85rem;">${data.category}</div>
        </div>
        <div>
          <div class="summary-stat-label">Unit Cost</div>
          <div class="summary-stat-value">${formatCurrency(data.unit_cost)}</div>
        </div>
        <div>
          <div class="summary-stat-label">Current Stock</div>
          <div class="summary-stat-value">${data.current_stock} pcs</div>
        </div>
        <div>
          <div class="summary-stat-label">Total Value</div>
          <div class="summary-stat-value">${formatCurrency(data.total_value)}</div>
        </div>
        <div>
          <div class="summary-stat-label">Supplier</div>
          <div class="summary-stat-value" style="font-size: 0.85rem;">${data.supplier_name}</div>
        </div>
      </div>

      <h4 style="margin-top: 0.5rem; font-size: 0.95rem; font-weight: 700; color: var(--navy-dark);">
        Transaction Ledger (${data.transactions_count} Entries)
      </h4>

      <table class="ledger-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th style="text-align: right;">Quantity</th>
            <th style="text-align: right;">Unit Cost</th>
            <th style="text-align: right;">Value</th>
            <th>Original Log Entry</th>
          </tr>
        </thead>
        <tbody>
          ${txRows}
        </tbody>
      </table>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div style="color: #dc2626; padding: 1rem;">Failed to load product details: ${err.message}</div>`;
  }
}

function closeProductLedgerModal() {
  document.getElementById('ledgerModal').classList.remove('open');
}

let currentInspectedSupplier = null;

function getHorizonLabel(h) {
  const map = {
    '1w': 'Past 7 Days',
    '2w': 'Past 14 Days',
    '1m': 'Past 30 Days',
    '3m': 'Past 90 Days',
    '6m': 'Past 180 Days',
    '12m': 'Past 365 Days',
    'all': 'All-Time Inception'
  };
  return map[h] || h;
}

async function openSupplierDetailModal(supplierName) {
  if (!supplierName) return;
  currentInspectedSupplier = supplierName;

  const modal = document.getElementById('supplierModal');
  const title = document.getElementById('supplierModalTitle');
  const subtitle = document.getElementById('supplierModalSubtitle');
  const soldTbody = document.getElementById('supSoldTableBody');
  const invTbody = document.getElementById('supInvTableBody');

  title.textContent = `${supplierName} — Performance & Inventory Breakdown`;
  subtitle.textContent = `Analyzing ${getHorizonLabel(state.horizon)} window ending ${state.asOfDate}`;

  // Reset KPI cards to loading
  document.getElementById('supModalSkus').textContent = '...';
  document.getElementById('supModalTotalVal').textContent = '...';
  document.getElementById('supModalUnitsSold').textContent = '...';
  document.getElementById('supModalCogs').textContent = '...';
  document.getElementById('supModalTurnover').textContent = '...';
  document.getElementById('supModalDsi').textContent = '...';

  soldTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">Loading sold products & turnover drivers...</td></tr>';
  invTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">Loading complete inventory...</td></tr>';

  modal.classList.add('open');

  try {
    const res = await fetch(`/api/analytics/supplier-detail?supplier_name=${encodeURIComponent(supplierName)}&horizon=${state.horizon}&as_of=${state.asOfDate}`);
    const data = await res.json();
    const sum = data.summary;

    // 1. Update KPI Header
    document.getElementById('supModalSkus').textContent = sum.sku_count;
    document.getElementById('supModalTotalVal').textContent = formatCurrency(sum.total_inventory_value);
    document.getElementById('supModalUnitsSold').textContent = formatNumber(sum.units_sold);
    document.getElementById('supModalCogs').textContent = formatCurrency(sum.cogs);
    document.getElementById('supModalTurnover').textContent = `${sum.turnover_ratio}x`;
    document.getElementById('supModalDsi').textContent = sum.average_dsi !== null ? `${sum.average_dsi} days` : '—';

    // Update Tab Badges
    document.getElementById('supSoldBadgeCount').textContent = data.sold_products.length;
    document.getElementById('supInvBadgeCount').textContent = data.inventory_products.length;

    // 2. Populate Sold Products & Turnover Drivers Table
    if (data.sold_products.length === 0) {
      soldTbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">No sales recorded for ${supplierName} in this time horizon (${getHorizonLabel(state.horizon)}).</td></tr>`;
    } else {
      soldTbody.innerHTML = '';
      data.sold_products.forEach(p => {
        const tr = document.createElement('tr');
        const badgeClass = `badge-${p.velocity_tier}`;
        tr.innerHTML = `
          <td><strong>${p.product_name}</strong></td>
          <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${p.category}</span></td>
          <td style="text-align: right;">${formatCurrency(p.unit_cost)}</td>
          <td style="text-align: right;">${formatNumber(p.current_stock)}</td>
          <td style="text-align: right; font-weight: 700; color: #2563eb;">${formatNumber(p.units_sold)}</td>
          <td style="text-align: right; font-weight: 700; color: #059669;">${formatCurrency(p.cogs)}</td>
          <td style="text-align: right; font-weight: 600;">${p.turnover_ratio}x</td>
          <td style="text-align: right;">
            <span class="impact-badge">${p.turnover_impact_pct}%</span>
          </td>
          <td><span class="badge-tier ${badgeClass}">${p.velocity_tier.toUpperCase()}</span></td>
        `;
        soldTbody.appendChild(tr);
      });
    }

    // 3. Populate Complete Active Inventory & Valuation Table
    if (data.inventory_products.length === 0) {
      invTbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">No active inventory recorded for this supplier.</td></tr>`;
    } else {
      invTbody.innerHTML = '';
      data.inventory_products.forEach(p => {
        const tr = document.createElement('tr');
        const badgeClass = `badge-${p.velocity_tier}`;
        tr.innerHTML = `
          <td><strong>${p.product_name}</strong></td>
          <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${p.category}</span></td>
          <td style="text-align: right;">${formatCurrency(p.unit_cost)}</td>
          <td style="text-align: right; font-weight: 700;">${formatNumber(p.current_stock)}</td>
          <td style="text-align: right; font-weight: 700; color: var(--navy-primary);">${formatCurrency(p.total_value)}</td>
          <td style="text-align: right; color: ${p.units_sold > 0 ? '#2563eb' : 'var(--text-muted)'}; font-weight: ${p.units_sold > 0 ? '700' : 'normal'};">
            ${p.units_sold > 0 ? formatNumber(p.units_sold) : '0'}
          </td>
          <td><span class="badge-tier ${badgeClass}">${p.velocity_tier.toUpperCase()}</span></td>
        `;
        invTbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Error loading supplier details:', err);
    soldTbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: #dc2626;">Failed to load supplier details: ${err.message}</td></tr>`;
  }
}

function closeSupplierModal() {
  currentInspectedSupplier = null;
  const modal = document.getElementById('supplierModal');
  if (modal) modal.classList.remove('open');
}

function switchSupplierSubTab(tabName) {
  const btnSold = document.getElementById('btnSupSoldTab');
  const btnInv = document.getElementById('btnSupInvTab');
  const viewSold = document.getElementById('supSoldTableView');
  const viewInv = document.getElementById('supInvTableView');

  if (tabName === 'sold') {
    btnSold.classList.add('active');
    btnInv.classList.remove('active');
    viewSold.style.display = 'block';
    viewInv.style.display = 'none';
  } else {
    btnInv.classList.add('active');
    btnSold.classList.remove('active');
    viewInv.style.display = 'block';
    viewSold.style.display = 'none';
  }
}

async function populateDropdownFilters() {
  try {
    const [catRes, supRes] = await Promise.all([
      fetch('/api/inventory/categories'),
      fetch('/api/inventory/suppliers')
    ]);
    const categories = await catRes.json();
    const suppliers = await supRes.json();

    const catSelect = document.getElementById('categoryFilter');
    categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      catSelect.appendChild(opt);
    });

    const supSelect = document.getElementById('supplierFilter');
    suppliers.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      supSelect.appendChild(opt);
    });
  } catch (err) {
    console.error('Error populating filters:', err);
  }
}

async function triggerDefaultCsvIngestion() {
  const btn = document.getElementById('syncDefaultBtn');
  btn.disabled = true;
  btn.textContent = 'Syncing...';

  try {
    const res = await fetch('/api/ingest/default-csv', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(`Synced ${data.products_created_or_updated} products & ${data.transactions_recorded} transactions!`);
      if (data.max_date) {
        state.asOfDate = data.max_date;
        document.getElementById('asOfDateInput').value = data.max_date;
      }
      refreshAll();
    } else {
      alert('Ingestion error: ' + data.message);
    }
  } catch (err) {
    alert('Ingestion failed: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>⚡</span> Ingest / Sync CSV';
  }
}

function refreshAll() {
  fetchKPIs();
  fetchTopProducts();
  fetchTopSuppliers();
  fetchVisualCharts();
  fetchProductTable();
  fetchAIInsights();
  if (currentInspectedSupplier) {
    openSupplierDetailModal(currentInspectedSupplier);
  }
}

async function fetchAIInsights() {
  try {
    const res = await fetch(`/api/forecast/insights?as_of=${state.asOfDate}`);
    const data = await res.json();

    const p1 = data.pillar1_stockout_alerts;
    const p2 = data.pillar2_purchase_orders;
    const p3 = data.pillar3_surging_momentum;
    const p4 = data.pillar4_trapped_capital;

    // 1. Update 4 Pillar KPI cards
    document.getElementById('aiStockoutCount').textContent = p1.count;
    document.getElementById('aiStockoutCritical').textContent = `${p1.critical_count} Critical (≤3d)`;
    document.getElementById('aiPoBudget').textContent = formatCurrency(p2.total_budget);
    document.getElementById('aiPoSkusBadge').textContent = `${p2.total_skus} SKUs`;
    document.getElementById('aiSurgingCount').textContent = `${p3.count} SKUs`;
    document.getElementById('aiDeadCapital').textContent = formatCurrency(p4.total_value);

    // 2. Populate Stockout Watchlist
    const soList = document.getElementById('stockoutRiskList');
    if (soList) {
      if (!p1.items || p1.items.length === 0) {
        soList.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">No immediate stockouts detected!</div>';
      } else {
        soList.innerHTML = '';
        p1.items.forEach((item, idx) => {
          const daysLeft = item.days_to_stockout !== null ? Math.round(item.days_to_stockout) : '0';
          const isCritical = item.days_to_stockout <= 3.0;
          const badgeClass = isCritical ? 'badge-dead' : 'badge-slow';
          
          const el = document.createElement('div');
          el.className = 'leaderboard-item';
          el.style.cursor = 'pointer';
          el.onclick = () => {
            document.getElementById('forecastProductSelect').value = item.id;
            fetchProductForecast(item.id);
            window.scrollTo({ top: 380, behavior: 'smooth' });
          };
          el.innerHTML = `
            <div class="leaderboard-rank rank-${idx < 3 ? idx + 1 : 'default'}">${idx + 1}</div>
            <div class="leaderboard-details">
              <div class="leaderboard-title">${item.product_name}</div>
              <div class="leaderboard-meta">
                <span>📦 Stock: ${item.current_stock} pcs</span>
                <span>🔥 Daily Burn: ${item.daily_burn_rate} pcs/day</span>
                <span>🏢 ${item.supplier_name}</span>
              </div>
            </div>
            <div class="leaderboard-metrics">
              <div class="badge-tier ${badgeClass}">${daysLeft} Days Left</div>
              <div class="metric-secondary" style="margin-top: 0.2rem; color: #059669; font-weight: 600;">
                Order: +${item.suggested_reorder_qty} pcs
              </div>
            </div>
          `;
          soList.appendChild(el);
        });
      }
    }

    // 3. Populate Supplier Purchase Orders List
    const poList = document.getElementById('supplierPoList');
    if (poList) {
      if (!p2.suppliers || p2.suppliers.length === 0) {
        poList.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">All inventory stock levels are healthy!</div>';
      } else {
        poList.innerHTML = '';
        p2.suppliers.slice(0, 10).forEach((sup, idx) => {
          const el = document.createElement('div');
          el.className = 'leaderboard-item';
          el.innerHTML = `
            <div class="leaderboard-rank rank-${idx < 3 ? idx + 1 : 'default'}">${idx + 1}</div>
            <div class="leaderboard-details">
              <div class="leaderboard-title">${sup.supplier_name}</div>
              <div class="leaderboard-meta">
                <span>📦 Needs Replenishment: <strong>${sup.sku_count} SKUs</strong></span>
                <span>Total Units: ${formatNumber(sup.total_units)} pcs</span>
              </div>
            </div>
            <div class="leaderboard-metrics">
              <div class="metric-primary" style="color: #059669;">${formatCurrency(sup.total_cost)}</div>
              <div class="metric-secondary">Est. PO Budget</div>
            </div>
          `;
          poList.appendChild(el);
        });
      }
    }

    // Populate product selector dropdown if empty
    populateForecastProductDropdown(allProductsList);
  } catch (err) {
    console.error('Error fetching AI insights:', err);
  }
}

let allProductsList = [];

async function populateForecastProductDropdown() {
  const select = document.getElementById('forecastProductSelect');
  if (!select || select.options.length > 2) return;

  try {
    const res = await fetch('/api/forecast/product-list');
    const items = await res.json();
    if (items && items.length > 0) {
      select.innerHTML = '';
      items.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.product_name} (${p.category})`;
        select.appendChild(opt);
      });

      // Default to first product
      select.value = items[0].id;
      fetchProductForecast(items[0].id);
    }
  } catch (err) {
    console.error('Error populating forecast dropdown:', err);
  }
}

async function fetchProductForecast(productId) {
  if (!productId) return;
  try {
    const res = await fetch(`/api/forecast/product/${productId}?as_of=${state.asOfDate}`);
    const data = await res.json();

    // 1. Update Diagnostic Badges
    document.getElementById('fcPatternBadge').textContent = `${data.pattern} (ADI ${data.adi || ''})`;
    document.getElementById('fcTrendBadge').textContent = `${data.trend} (x${data.momentum || '1.0'})`;
    
    const stockoutEl = document.getElementById('fcDaysStockout');
    if (data.days_to_stockout !== null) {
      stockoutEl.textContent = `${Math.round(data.days_to_stockout)} Days Remaining`;
      stockoutEl.style.color = data.days_to_stockout <= 7 ? '#dc2626' : '#ea580c';
    } else {
      stockoutEl.textContent = 'Ample Stock / No Burn';
      stockoutEl.style.color = '#059669';
    }

    document.getElementById('fcSuggestedOrder').textContent = data.suggested_reorder_qty > 0 
      ? `+${data.suggested_reorder_qty} pcs (14d Target)`
      : '0 pcs (Sufficient Stock)';

    document.getElementById('fcEstimatedCost').textContent = formatCurrency(data.estimated_po_cost);

    // 2. Render Interactive Trajectory Chart
    renderForecastTrajectoryChart(data);
  } catch (err) {
    console.error('Error fetching product forecast:', err);
  }
}

// Event Listeners Initialization
document.addEventListener('DOMContentLoaded', () => {
  // 1. Horizon Pills
  document.querySelectorAll('.horizon-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      document.querySelectorAll('.horizon-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.horizon = pill.dataset.horizon;
      refreshAll();
    });
  });

  // 2. As-Of Date Change
  const dateInput = document.getElementById('asOfDateInput');
  dateInput.value = state.asOfDate;
  dateInput.addEventListener('change', (e) => {
    state.asOfDate = e.target.value;
    refreshAll();
  });

  // 3. Product Top-Sellers Mode Toggle (Volume vs Value)
  document.querySelectorAll('.prod-toggle-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.prod-toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.productSortMode = btn.dataset.sort;
      fetchTopProducts();
    });
  });

  // 4. Supplier Top-Sellers Mode Toggle (Volume vs Value)
  document.querySelectorAll('.sup-toggle-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.sup-toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.supplierSortMode = btn.dataset.sort;
      fetchTopSuppliers();
    });
  });

  // 5. View Tabs Navigation
  document.querySelectorAll('.view-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
      tab.classList.add('active');
      const targetId = tab.dataset.target;
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.classList.add('active');
      }

      if (targetId === 'tab-forecasting') {
        const select = document.getElementById('forecastProductSelect');
        if (select && select.value) {
          fetchProductForecast(select.value);
        } else {
          populateForecastProductDropdown();
        }
      }
    });
  });

  // 6. Search & Filters for Product Table
  let searchTimeout = null;
  document.getElementById('tableSearchInput').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.tableSearch = e.target.value;
      state.tablePage = 1;
      fetchProductTable();
    }, 300);
  });

  document.getElementById('categoryFilter').addEventListener('change', (e) => {
    state.tableCategory = e.target.value;
    state.tablePage = 1;
    fetchProductTable();
  });

  document.getElementById('supplierFilter').addEventListener('change', (e) => {
    state.tableSupplier = e.target.value;
    state.tablePage = 1;
    fetchProductTable();
  });

  document.getElementById('velocityFilter').addEventListener('change', (e) => {
    state.tableVelocity = e.target.value;
    state.tablePage = 1;
    fetchProductTable();
  });

  // 7. Pagination
  document.getElementById('prevPageBtn').addEventListener('click', () => {
    if (state.tablePage > 1) {
      state.tablePage--;
      fetchProductTable();
    }
  });

  document.getElementById('nextPageBtn').addEventListener('click', () => {
    state.tablePage++;
    fetchProductTable();
  });

  // 8. CSV Ingest button
  document.getElementById('syncDefaultBtn').addEventListener('click', triggerDefaultCsvIngestion);

  // 8b. Upload Custom CSV button
  const uploadBtn = document.getElementById('uploadCsvBtn');
  const fileInput = document.getElementById('csvFileInput');

  uploadBtn.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span>⏳</span> Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/ingest/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Ingested ${data.products_created_or_updated} products & ${data.transactions_recorded} transactions!`);
        if (data.max_date) {
          state.asOfDate = data.max_date;
          document.getElementById('asOfDateInput').value = data.max_date;
        }
        refreshAll();
      } else {
        alert('Upload error: ' + data.message);
      }
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.innerHTML = '<span>📁</span> Upload CSV';
      fileInput.value = '';
    }
  });

  // 8c. Forecast Product Selector Change
  const fcSelect = document.getElementById('forecastProductSelect');
  if (fcSelect) {
    fcSelect.addEventListener('change', (e) => {
      fetchProductForecast(e.target.value);
    });
  }

  // 8d. Retrain AI Models Button
  const retrainBtn = document.getElementById('retrainAiBtn');
  if (retrainBtn) {
    retrainBtn.addEventListener('click', async () => {
      retrainBtn.disabled = true;
      retrainBtn.innerHTML = '<span>⏳</span> Retraining Models...';
      try {
        const res = await fetch(`/api/forecast/retrain?as_of=${state.asOfDate}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          showToast('AI Demand & Forecasting models retrained successfully!');
          fetchAIInsights();
          if (fcSelect && fcSelect.value) {
            fetchProductForecast(fcSelect.value);
          }
        } else {
          alert('Retrain error');
        }
      } catch (err) {
        alert('Retrain failed: ' + err.message);
      } finally {
        retrainBtn.disabled = false;
        retrainBtn.innerHTML = '<span>⚡</span> Retrain AI Models';
      }
    });
  }

  // 8e. Modal Backdrop and Escape Key Close Listeners
  window.addEventListener('click', (e) => {
    const sm = document.getElementById('supplierModal');
    if (e.target === sm) closeSupplierModal();
    const lm = document.getElementById('ledgerModal');
    if (e.target === lm) closeProductLedgerModal();
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSupplierModal();
      closeProductLedgerModal();
    }
  });

  // 9. Initial Load
  populateDropdownFilters();
  refreshAll();
});
