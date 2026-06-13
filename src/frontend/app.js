// ===== DC Hounds — frontend logic =====
// Talks to the FastAPI model server. All scoring lives server-side.

const API = 'http://127.0.0.1:8000';

// Column definitions (lower = better for all). No per-year labels — cost is capital.
const COLUMNS = {
  congestion_alpha:   { label: 'Congestion',   short: 'congestion',   fmt: v => (v * 100).toFixed(1) + '%' },
  dc_carbon_tco2_yr:  { label: 'CO₂',          short: 'CO₂',          fmt: v => fmtNum(v) + ' tCO₂' },
  total_cost_eur:     { label: 'Cost',         short: 'cost',         fmt: v => fmtEur(v) },
  connectivity_score: { label: 'Connectivity', short: 'connectivity', fmt: v => v.toFixed(3) },
  balance_score:      { label: 'Aggregate',    short: 'aggregate',    fmt: v => v.toFixed(3) },
};
const RAW_TABS = ['congestion_alpha', 'dc_carbon_tco2_yr', 'total_cost_eur', 'connectivity_score'];
const RANKED_TABS = [...RAW_TABS, 'balance_score'];

// prioritize dropdown -> default view after a run
const PRIO_MAP = {
  balanced:   { mode: 'ranked', tab: 'balance_score' },
  cost:       { mode: 'raw',    tab: 'total_cost_eur' },
  co2:        { mode: 'raw',    tab: 'dc_carbon_tco2_yr' },
  congestion: { mode: 'raw',    tab: 'congestion_alpha' },
};

// State
let map = null;
let markerLayer = null;      // Leaflet LayerGroup holding all node dots
let markerMap = {};          // node_id -> circleMarker
let coordsById = {};         // node_id -> { lat, lng, country }
let allNodes = [];           // /results/raw  (scores + country, NO coords)
let balanceNodes = [];       // /results/balance (top10 normalized + balance_score + country)
let activeMode = 'raw';
let activeTab = 'congestion_alpha';
let activePrio = 'balanced';
let hasRun = false;

const GREY = { fillColor: '#475569', color: '#64748b', weight: 1, radius: 5, fillOpacity: 0.55, opacity: 0.6 };
const HOT  = { fillColor: '#f59e0b', color: '#fbbf24', weight: 3, radius: 9, fillOpacity: 0.95, opacity: 1 };

// ---------- formatting ----------
function fmtNum(v) { return Math.round(v).toLocaleString('en-US'); }
function fmtEur(v) {
  if (v >= 1e9) return '€' + (v / 1e9).toFixed(2) + 'B';
  if (v >= 1e6) return '€' + (v / 1e6).toFixed(2) + 'M';
  if (v >= 1e3) return '€' + (v / 1e3).toFixed(1) + 'k';
  return '€' + Math.round(v).toLocaleString('en-US');
}

function showLoading(show, sub) {
  document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
  if (sub) document.getElementById('loader-sub').textContent = sub;
}

// ---------- run flow ----------
async function runModel() {
  const capacity_mw = parseFloat(document.getElementById('in-capacity').value);
  const surface_m2  = parseFloat(document.getElementById('in-surface').value);
  if (!(capacity_mw > 0) || !(surface_m2 > 0)) {
    alert('Enter positive values for capacity and footprint.');
    return;
  }

  showLoading(true, 'Filtering nodes by capacity constraint');
  try {
    const runRes = await fetch(`${API}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capacity_mw, surface_m2 }),
    });
    if (!runRes.ok) {
      const err = await runRes.json().catch(() => ({}));
      throw new Error(err.detail || `Run failed (${runRes.status})`);
    }
    showLoading(true, 'Scoring surviving nodes');

    const [coords, raw, balance] = await Promise.all([
      fetch(`${API}/nodes`).then(r => r.json()),
      fetch(`${API}/results/raw`).then(r => r.json()),
      fetch(`${API}/results/balance`).then(r => r.json()),
    ]);

    coordsById = {};
    coords.forEach(n => { coordsById[n.node_id] = { lat: n.lat, lng: n.lng, country: n.country }; });
    allNodes = raw;
    balanceNodes = balance;

    // apply prioritize selection -> default view
    const prio = PRIO_MAP[activePrio] || PRIO_MAP.balanced;
    activeMode = prio.mode;
    activeTab = prio.tab;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === activeMode));

    populateMarkers(!hasRun);   // fit bounds only on first run
    hasRun = true;

    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('results-ui').style.display = 'flex';
    document.getElementById('map-legend').style.display = 'flex';

    renderTabs();
    render();
  } catch (err) {
    alert(err.message || 'Could not reach the model server. Is it running on :8000?');
  } finally {
    showLoading(false);
  }
}

// ---------- map ----------
function createMap() {
  map = L.map('europe-map', {
    zoomControl: true, minZoom: 4, maxZoom: 9,
    maxBounds: [[33, -28], [72, 45]], maxBoundsViscosity: 1.0,
  }).setView([54, 12], 4);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd', maxZoom: 9,
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);
}

function populateMarkers(fit) {
  markerLayer.clearLayers();
  markerMap = {};
  const bounds = [];
  allNodes.forEach(n => {
    const c = coordsById[n.node_id];
    if (!c || c.lat == null || c.lng == null) return;
    const m = L.circleMarker([c.lat, c.lng], GREY);
    m.bindTooltip(nodeTooltip(n, c), { direction: 'top', className: 'node-tip', sticky: true });
    markerLayer.addLayer(m);
    markerMap[n.node_id] = m;
    bounds.push([c.lat, c.lng]);
  });
  if (fit && bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 });
}

// full raw-row tooltip
function nodeTooltip(n, c) {
  const rows = RAW_TABS.map(col =>
    `<div class="tt-row"><span>${COLUMNS[col].label}</span><b>${n[col] != null ? COLUMNS[col].fmt(n[col]) : '—'}</b></div>`
  ).join('');
  return `<div class="tt-head">${n.node_id}<span>${(c && c.country) || n.country || ''}</span></div>${rows}`;
}

function updateMapHighlights(top10Ids) {
  const top = new Set(top10Ids);
  Object.entries(markerMap).forEach(([id, m]) => {
    m.setStyle(top.has(id) ? HOT : GREY);
    if (top.has(id)) m.bringToFront();
  });
}

// ---------- ranking ----------
function sortedByCol(rows, col) {
  return [...rows].filter(r => r[col] != null).sort((a, b) => a[col] - b[col]);
}

// ---------- controls ----------
function initControls() {
  document.getElementById('btn-go').addEventListener('click', runModel);
  ['in-capacity', 'in-surface'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') runModel(); });
  });

  // prioritize dropdown
  const trigger = document.getElementById('prio-trigger');
  const menu = document.getElementById('prio-menu');
  const text = document.getElementById('prio-text');
  trigger.addEventListener('click', e => {
    e.stopPropagation();
    const open = menu.style.display === 'flex';
    menu.style.display = open ? 'none' : 'flex';
    trigger.classList.toggle('open', !open);
  });
  document.addEventListener('click', () => { menu.style.display = 'none'; trigger.classList.remove('open'); });
  menu.querySelectorAll('.sb-dd-item').forEach(item => {
    item.addEventListener('click', e => {
      e.stopPropagation();
      activePrio = item.dataset.prio;
      text.textContent = item.textContent;
      menu.querySelectorAll('.sb-dd-item').forEach(i => i.classList.toggle('active', i === item));
      menu.style.display = 'none';
      trigger.classList.remove('open');
    });
  });

  // mode toggle
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;
      if (mode === activeMode) return;
      activeMode = mode;
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
      if (activeMode === 'raw' && activeTab === 'balance_score') activeTab = 'congestion_alpha';
      renderTabs();
      render();
    });
  });
}

function currentTabs() { return activeMode === 'ranked' ? RANKED_TABS : RAW_TABS; }

function renderTabs() {
  const bar = document.getElementById('tabs-bar');
  bar.innerHTML = currentTabs().map(col =>
    `<button class="tab-btn${col === activeTab ? ' active' : ''}" data-col="${col}">${COLUMNS[col].label}</button>`
  ).join('');
  bar.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.col;
      bar.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.col === activeTab));
      render();
    });
  });
  document.getElementById('mode-hint').textContent = activeMode === 'raw'
    ? 'All viable nodes, sorted best-first on the selected metric. Top 10 highlighted on map.'
    : 'Top 10 nodes per metric. Aggregate ranks the best all-round balance.';
}

// ---------- render ----------
function render() {
  const col = activeTab;
  const isAggregate = (col === 'balance_score');
  const source = isAggregate ? balanceNodes : allNodes;
  const sorted = sortedByCol(source, col);
  const rows = (activeMode === 'ranked' || isAggregate) ? sorted.slice(0, 10) : sorted;

  const top10Ids = sorted.slice(0, 10).map(r => r.node_id);
  updateMapHighlights(top10Ids);

  document.getElementById('legend-tab').textContent = COLUMNS[col].short;
  document.getElementById('ph-val-label').textContent = COLUMNS[col].label;

  const top10Set = new Set(top10Ids);
  const list = document.getElementById('node-list');
  list.innerHTML = rows.map((r, i) => {
    const c = coordsById[r.node_id] || {};
    const country = r.country || c.country || '—';
    const hot = top10Set.has(r.node_id);
    return `
      <div class="node-row${hot ? ' highlight' : ''}" data-node="${r.node_id}">
        <span class="nr-rank">${i + 1}</span>
        <span class="nr-id"><span class="nr-name">${r.node_id}</span><span class="nr-country">${country}</span></span>
        <span class="nr-val">${COLUMNS[col].fmt(r[col])}</span>
      </div>`;
  }).join('');

  list.querySelectorAll('.node-row').forEach(row => {
    const id = row.dataset.node;
    const m = markerMap[id];
    if (!m) return;
    row.addEventListener('mouseenter', () => m.openTooltip());
    row.addEventListener('mouseleave', () => m.closeTooltip());
    row.addEventListener('click', () => {
      const c = coordsById[id];
      if (c && c.lat != null) map.setView([c.lat, c.lng], 7, { animate: true });
      m.openTooltip();
    });
  });
}

// ---------- boot ----------
window.addEventListener('DOMContentLoaded', () => {
  createMap();
  initControls();
});
