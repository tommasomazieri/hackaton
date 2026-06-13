// ===== DC Hounds — frontend logic =====
// Talks to the FastAPI model server. All scoring lives server-side.

const API = 'http://127.0.0.1:8000';

// Column definitions (lower = better for all). No per-year labels — cost is capital.
const COLUMNS = {
  congestion_alpha:   { label: 'Congestion',   short: 'congestion',   fmt: v => (v * 100).toFixed(1) + '%' },
  dc_carbon_tco2_yr:  { label: 'CO₂',          short: 'CO₂',          fmt: v => fmtNum(v) + ' tCO₂' },
  total_cost_eur:     { label: 'Cost',         short: 'cost',         fmt: v => fmtEur(v) },
  connectivity_score: { label: 'Connectivity', short: 'connectivity', fmt: v => v.toFixed(3) },
};
// The 4 scored metrics — these are the table's weight-editable columns.
const METRIC_COLS = ['congestion_alpha', 'dc_carbon_tco2_yr', 'total_cost_eur', 'connectivity_score'];

// Extra fields shown ONLY in the map hover popup (not in the ranked table).
// Cost split + consumption stats — sourced from /results/detail.
const DETAIL_ROWS = [
  { key: 'area_km2',            label: 'Area (proxy)',    fmt: v => fmtNum(v) + ' km²' },
  { key: 'energy_cost_eur',     label: 'Energy cost',     fmt: v => fmtEur(v) },
  { key: 'land_cost_eur',       label: 'Land cost',       fmt: v => fmtEur(v) },
  { key: 'consumption_mean_mw', label: 'Consumption μ',   fmt: v => fmtNum(v) + ' MW' },
  { key: 'consumption_std_mw',  label: 'Consumption σ',   fmt: v => (+v).toFixed(1) + ' MW' },
];

// State
let map = null;
let markerLayer = null;      // Leaflet LayerGroup holding all node dots
let markerMap = {};          // node_id -> circleMarker
let coordsById = {};         // node_id -> { lat, lng, country }
let allNodes = [];           // /results/raw  (scores + country, NO coords) — drives markers
let detailById = {};         // node_id -> /results/detail row (full breakdown for popup)
let rankedNodes = [];        // POST /results/ranked (top10 raw rows, best-first)
let appliedWeights = {};     // weights last sent to backend (default 1/n each)
let pendingWeights = {};     // working copy edited via the column headers
let hasRun = false;
let hoverTimer = null;
let activeTooltipMarker = null;
let mapMoving = false;

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

// ---------- weights ----------
function initWeights() {
  const w = 1 / METRIC_COLS.length;
  appliedWeights = {};
  pendingWeights = {};
  METRIC_COLS.forEach(c => { appliedWeights[c] = w; pendingWeights[c] = w; });
}
function weightsSum(w) { return METRIC_COLS.reduce((s, c) => s + (w[c] || 0), 0); }
function isDirty() { return METRIC_COLS.some(c => Math.abs(pendingWeights[c] - appliedWeights[c]) > 1e-9); }

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

    const [coords, raw, detail] = await Promise.all([
      fetch(`${API}/nodes`).then(r => r.json()),
      fetch(`${API}/results/raw`).then(r => r.json()),
      fetch(`${API}/results/detail`).then(r => r.json()),
    ]);

    coordsById = {};
    coords.forEach(n => { coordsById[n.node_id] = { lat: n.lat, lng: n.lng, country: n.country }; });
    allNodes = raw;
    detailById = {};
    detail.forEach(n => { detailById[n.node_id] = n; });

    populateMarkers(!hasRun);   // fit bounds only on first run
    hasRun = true;

    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('results-ui').style.display = 'flex';
    document.getElementById('map-legend').style.display = 'flex';

    renderHeader();
    await fetchRanked(appliedWeights);   // populates rankedNodes -> render()
  } catch (err) {
    alert(err.message || 'Could not reach the model server. Is it running on :8000?');
  } finally {
    showLoading(false);
  }
}

// POST current weights, store the top-10 ranked rows, re-render the table.
async function fetchRanked(weights) {
  try {
    const res = await fetch(`${API}/results/ranked`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weights }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ranking failed (${res.status})`);
    }
    rankedNodes = await res.json();
    console.debug('[rank] applied', weights, '→ top:', rankedNodes.map(r => r.node_id));
    render();
  } catch (err) {
    alert(err.message || 'Could not compute ranking.');
  }
}

// ---------- map ----------
function createMap() {
  map = L.map('europe-map', {
    zoomControl: true, minZoom: 4, maxZoom: 9,
    maxBounds: [[33, -28], [72, 45]], maxBoundsViscosity: 1.0,
    inertia: false,
  }).setView([54, 12], 4);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd', maxZoom: 9,
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);
  map.on('dragstart', () => { mapMoving = true; clearHoverTimer(); closeActiveTooltip(); });
  map.on('dragend', () => { map.panInsideBounds([[33, -28], [72, 45]], { animate: false }); });
  map.on('moveend zoomend', () => { mapMoving = false; refreshTipDirections(); });
}

function clearHoverTimer() {
  if (hoverTimer) { clearTimeout(hoverTimer); hoverTimer = null; }
}
function closeActiveTooltip() {
  if (activeTooltipMarker) { activeTooltipMarker.closeTooltip(); activeTooltipMarker = null; }
}

function populateMarkers(fit) {
  markerLayer.clearLayers();
  markerMap = {};
  const bounds = [];
  allNodes.forEach(n => {
    const c = coordsById[n.node_id];
    if (!c || c.lat == null || c.lng == null) return;
    const m = L.circleMarker([c.lat, c.lng], GREY);
    m.bindTooltip(nodeTooltip(n, c), { direction: tipDirection(c.lat, c.lng), className: 'node-tip' });
    m.on('mouseover', () => {
      if (mapMoving) return;
      clearHoverTimer();
      hoverTimer = setTimeout(() => {
        if (mapMoving) return;
        closeActiveTooltip();
        activeTooltipMarker = m;
        m.openTooltip();
      }, 1000);
    });
    m.on('mouseout', () => { clearHoverTimer(); closeActiveTooltip(); });
    markerLayer.addLayer(m);
    markerMap[n.node_id] = m;
    bounds.push([c.lat, c.lng]);
  });
  if (fit && bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 });
}

// Popup opens above the node by default; if that would tuck it under the fixed
// header, open it below instead. Recomputed on pan/zoom.
function tipDirection(lat, lng) {
  const header = document.querySelector('header');
  const headerH = header ? header.offsetHeight : 0;
  const TIP_H = 200;  // worst-case popup height incl. detail rows
  const y = map.latLngToContainerPoint([lat, lng]).y;
  return (y - TIP_H) < headerH ? 'bottom' : 'top';
}

function refreshTipDirections() {
  Object.values(markerMap).forEach(m => {
    const tip = m.getTooltip();
    if (!tip) return;
    const ll = m.getLatLng();
    tip.options.direction = tipDirection(ll.lat, ll.lng);
    if (m.isTooltipOpen()) m.openTooltip();  // re-place an open popup
  });
}

// hover popup — raw scores PLUS the detail breakdown (cost split + consumption)
function nodeTooltip(n, c) {
  const rows = METRIC_COLS.map(col =>
    `<div class="tt-row"><span>${COLUMNS[col].label}</span><b>${n[col] != null ? COLUMNS[col].fmt(n[col]) : '—'}</b></div>`
  ).join('');

  const d = detailById[n.node_id];
  let extra = '';
  if (d) {
    const detailRows = DETAIL_ROWS
      .filter(r => d[r.key] != null)
      .map(r => `<div class="tt-row"><span>${r.label}</span><b>${r.fmt(d[r.key])}</b></div>`)
      .join('');
    if (detailRows) extra = `<div class="tt-sep"></div>${detailRows}`;
  }

  return `<div class="tt-head">${n.node_id}<span>${(c && c.country) || n.country || ''}</span></div>${rows}${extra}`;
}

function updateMapHighlights(topIds) {
  const top = new Set(topIds);
  Object.entries(markerMap).forEach(([id, m]) => {
    m.setStyle(top.has(id) ? HOT : GREY);
    if (top.has(id)) m.bringToFront();
  });
}

// ---------- controls ----------
function initControls() {
  document.getElementById('btn-go').addEventListener('click', runModel);
  ['in-capacity', 'in-surface'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') runModel(); });
  });

  // click outside an open weight popover closes it
  document.addEventListener('mousedown', e => {
    if (!e.target.closest('.weight-pop') && !e.target.closest('.col-head')) closeWeightInput();
  });
}

// ---------- column headers + weight editing ----------
function renderHeader() {
  const head = document.getElementById('panel-head');
  const dirty = isDirty();
  const sum = weightsSum(pendingWeights);
  const ok = Math.abs(sum - 1) < 0.005;             // global apply only at 100%
  const applyTitle = ok ? 'Apply weights' : `Weights total ${Math.round(sum * 100)}% — must be 100%`;

  head.innerHTML =
    `<span class="ph-rank">#</span><span class="ph-node">Node</span>` +
    METRIC_COLS.map(col => {
      const w = pendingWeights[col];
      const cdirty = Math.abs(w - appliedWeights[col]) > 1e-9;
      return `<span class="col-head${cdirty ? ' pending' : ''}" data-col="${col}" title="Double-click to set weight">
        <span class="ch-label">${COLUMNS[col].label}</span>
        <span class="weight-badge">${Math.round(w * 100)}%</span>
      </span>`;
    }).join('') +
    // global apply/discard — last grid cell, right of the whole header row
    `<span class="weight-actions" id="weight-actions" style="display:${dirty ? 'flex' : 'none'};">
      <button class="wa-btn wa-apply" id="wa-apply"${ok ? '' : ' disabled'} title="${applyTitle}">✓</button>
      <button class="wa-btn wa-discard" id="wa-discard" title="Discard">✗</button>
    </span>`;

  head.querySelectorAll('.col-head').forEach(cell => {
    cell.addEventListener('dblclick', () => openWeightInput(cell.dataset.col));
  });
  const applyBtn = document.getElementById('wa-apply');
  const discardBtn = document.getElementById('wa-discard');
  if (applyBtn) applyBtn.addEventListener('click', applyWeights);
  if (discardBtn) discardBtn.addEventListener('click', discardWeights);
}

// commit all staged weights (only valid when they total 100%)
function applyWeights() {
  if (Math.abs(weightsSum(pendingWeights) - 1) >= 0.005) return;
  appliedWeights = { ...pendingWeights };
  closeWeightInput();
  renderHeader();
  fetchRanked(appliedWeights);
}

// throw away staged edits, revert to last-applied weights
function discardWeights() {
  pendingWeights = { ...appliedWeights };
  closeWeightInput();
  renderHeader();
}

function closeWeightInput() {
  document.querySelectorAll('.weight-pop').forEach(p => p.remove());
}

function openWeightInput(col) {
  closeWeightInput();  // one at a time
  const cell = document.querySelector(`.col-head[data-col="${col}"]`);
  if (!cell) return;

  const pop = document.createElement('div');
  pop.className = 'weight-pop';
  pop.innerHTML = `
    <input type="number" min="0" max="100" step="1" class="wp-input" value="${Math.round(pendingWeights[col] * 100)}">
    <span class="wp-pct">%</span>
    <button class="wp-ok" title="Confirm">✓</button>
    <button class="wp-x" title="Close">✗</button>`;
  cell.appendChild(pop);

  const input = pop.querySelector('.wp-input');
  input.focus();
  input.select();

  const confirm = () => {
    const val = parseFloat(input.value);
    if (isNaN(val) || val < 0 || val > 100) { input.classList.add('err'); return; }
    // No sum check here — staging a single weight is free; the running total may
    // sit off 100% while editing. The global ✓ enforces 100% before applying.
    pendingWeights[col] = val / 100;
    closeWeightInput();
    renderHeader();
  };

  pop.querySelector('.wp-ok').addEventListener('click', confirm);
  pop.querySelector('.wp-x').addEventListener('click', closeWeightInput);
  input.addEventListener('input', () => input.classList.remove('err'));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') confirm();
    if (e.key === 'Escape') closeWeightInput();
  });
}

// ---------- render ----------
function render() {
  // Build the table FIRST so nothing downstream (map/legend) can block it.
  const list = document.getElementById('node-list');
  list.innerHTML = rankedNodes.map((r, i) => {
    const c = coordsById[r.node_id] || {};
    const country = r.country || c.country || '—';
    const cells = METRIC_COLS.map(col =>
      `<span class="nr-cell">${r[col] != null ? COLUMNS[col].fmt(r[col]) : '—'}</span>`
    ).join('');
    return `
      <div class="node-row" data-node="${r.node_id}">
        <span class="nr-rank">${i + 1}</span>
        <span class="nr-id"><span class="nr-name">${r.node_id}</span><span class="nr-country">${country}</span></span>
        ${cells}
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

  // map highlights + legend after the table is committed
  updateMapHighlights(rankedNodes.map(r => r.node_id));
  const legend = document.getElementById('legend-tab');
  if (legend) legend.textContent = 'weighted';
}

// ---------- boot ----------
window.addEventListener('DOMContentLoaded', () => {
  initWeights();
  createMap();
  initControls();
});
