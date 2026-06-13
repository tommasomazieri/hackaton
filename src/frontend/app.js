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

// Country ledger — ISO2 -> display name (the 27 countries the backend covers,
// matching COUNTRY_AREA_KM2 in src/model/01_load_filter.py).
const COUNTRIES = {
  AT: 'Austria', BE: 'Belgium', BG: 'Bulgaria', CY: 'Cyprus', CZ: 'Czech Republic',
  DE: 'Germany', DK: 'Denmark', EE: 'Estonia', ES: 'Spain', FI: 'Finland',
  FR: 'France', HR: 'Croatia', HU: 'Hungary', IE: 'Ireland', IT: 'Italy',
  LT: 'Lithuania', LU: 'Luxembourg', LV: 'Latvia', MT: 'Malta', NL: 'Netherlands',
  NO: 'Norway', PL: 'Poland', PT: 'Portugal', RO: 'Romania', SE: 'Sweden',
  SI: 'Slovenia', SK: 'Slovakia',
};
const VISIBLE_FLAGS = 5;                       // inline chips before the (…) overflow
const flagSrc = code => `flags/${code.toLowerCase()}.svg`;

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
let selectedCountries = [];   // ISO2 whitelist, insertion order. Empty = all countries.
let hoverTimer = null;
let activeTooltipMarker = null;
let mapMoving = false;
let reportMaps = [];         // Leaflet instances built for the report modal
let reportCharts = [];       // Chart.js instances built for the report modal

const GREY = { fillColor: '#475569', color: '#64748b', weight: 1, radius: 5, fillOpacity: 0.55, opacity: 0.6 };
const HOT  = { fillColor: '#f59e0b', color: '#fbbf24', weight: 3, radius: 9, fillOpacity: 0.95, opacity: 1 };
// Brighter/bigger grey for the report's static map so mainland nodes read clearly
// against the dark basemap (the live map can stay subtle; a printed page can't).
const REPORT_GREY = { fillColor: '#7c8aa5', color: '#aab6cc', weight: 1, radius: 6, fillOpacity: 0.8, opacity: 0.9 };

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
      body: JSON.stringify({ capacity_mw, surface_m2, countries: selectedCountries }),
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

// ---------- country ledger ----------
// Floating transparent pill hanging off the header's bottom edge. Curates the
// `selectedCountries` whitelist; any change after the first run re-runs the model.
function renderLedger() {
  const el = document.getElementById('country-ledger');
  if (!el) return;
  closeLedgerMenus();

  const sel = selectedCountries;
  const inline = sel.length <= VISIBLE_FLAGS ? sel : sel.slice(0, VISIBLE_FLAGS);
  const overflow = sel.length <= VISIBLE_FLAGS ? [] : sel.slice(VISIBLE_FLAGS);

  const chips = inline.map(code =>
    `<button class="cl-flag" data-code="${code}" title="${COUNTRIES[code]} — click to remove">
       <img src="${flagSrc(code)}" alt="${code}">
       <span class="cl-x">×</span>
     </button>`).join('');

  const overflowChip = overflow.length
    ? `<button class="cl-overflow" id="cl-overflow" title="${overflow.length} more selected">+${overflow.length}</button>`
    : '';

  const addChip = `<button class="cl-add" id="cl-add" title="Add a country">+</button>`;

  el.innerHTML = chips + overflowChip + addChip;

  el.querySelectorAll('.cl-flag').forEach(btn =>
    btn.addEventListener('click', () => removeCountry(btn.dataset.code)));
  const ov = document.getElementById('cl-overflow');
  if (ov) ov.addEventListener('click', e => { e.stopPropagation(); toggleOverflowMenu(); });
  document.getElementById('cl-add').addEventListener('click', e => { e.stopPropagation(); toggleAddMenu(); });
}

function addCountry(code) {
  if (!COUNTRIES[code] || selectedCountries.includes(code)) return;
  selectedCountries.push(code);
  onLedgerChange();
}

function removeCountry(code) {
  selectedCountries = selectedCountries.filter(c => c !== code);
  onLedgerChange();
}

function onLedgerChange() {
  renderLedger();
  if (hasRun) runModel();   // auto re-run with the new whitelist
}

// the + button menu — countries NOT yet selected (flag circle + name)
function toggleAddMenu() {
  const open = document.getElementById('cl-menu');
  if (open) { const was = open.dataset.owner; closeLedgerMenus(); if (was === 'add') return; }
  const remaining = Object.keys(COUNTRIES)
    .filter(c => !selectedCountries.includes(c))
    .sort((a, b) => COUNTRIES[a].localeCompare(COUNTRIES[b]));
  if (!remaining.length) return;
  const items = remaining.map(code =>
    `<button class="cl-menu-item" data-code="${code}">
       <img src="${flagSrc(code)}" alt="${code}"><span>${COUNTRIES[code]}</span>
     </button>`).join('');
  openLedgerMenu('add', items, code => addCountry(code));
}

// the (…) overflow menu — selected countries beyond the inline cap (removable)
function toggleOverflowMenu() {
  const open = document.getElementById('cl-menu');
  if (open) { const was = open.dataset.owner; closeLedgerMenus(); if (was === 'overflow') return; }
  const overflow = selectedCountries.slice(VISIBLE_FLAGS);
  if (!overflow.length) return;
  const items = overflow.map(code =>
    `<button class="cl-menu-item" data-code="${code}">
       <img src="${flagSrc(code)}" alt="${code}"><span>${COUNTRIES[code]}</span><b class="cl-mi-x">×</b>
     </button>`).join('');
  openLedgerMenu('overflow', items, code => removeCountry(code));
}

function openLedgerMenu(owner, itemsHtml, onPick) {
  closeLedgerMenus();
  const menu = document.createElement('div');
  menu.className = 'cl-menu';
  menu.id = 'cl-menu';
  menu.dataset.owner = owner;
  menu.innerHTML = itemsHtml;
  document.getElementById('country-ledger').appendChild(menu);
  menu.querySelectorAll('.cl-menu-item').forEach(item =>
    item.addEventListener('click', e => { e.stopPropagation(); onPick(item.dataset.code); }));
}

function closeLedgerMenus() {
  const m = document.getElementById('cl-menu');
  if (m) m.remove();
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
    if (!e.target.closest('#country-ledger')) closeLedgerMenus();
  });

  // report modal
  document.getElementById('btn-export').addEventListener('click', openReport);
  document.getElementById('report-download').addEventListener('click', downloadReportPDF);
  // close via delegation so nothing (print, re-render) can orphan the handler
  document.addEventListener('click', e => {
    if (e.target.closest('#report-close')) closeReport();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.getElementById('report-modal').classList.contains('open')) closeReport();
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

// ---------- export report ----------
function median(arr) {
  const a = arr.filter(v => v != null && !isNaN(v)).sort((x, y) => x - y);
  if (!a.length) return null;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function openReport() {
  if (!hasRun || !rankedNodes.length) return;
  const modal = document.getElementById('report-modal');
  document.getElementById('report-scroll').innerHTML = buildReport();
  modal.style.display = 'block';
  // let display:block apply, then add .open so the transform animates in
  requestAnimationFrame(() => {
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    // mount maps/charts only once the panel is laid out (Leaflet needs size)
    requestAnimationFrame(() => {
      buildReportMap();
      buildReportCharts();
      loadReportSiteImages();
    });
  });
}

function closeReport() {
  const modal = document.getElementById('report-modal');
  modal.classList.remove('open');                 // slides out (transform 0.35s)
  modal.setAttribute('aria-hidden', 'true');
  reportImgToken++;                               // stop any in-flight image loop
  setTimeout(() => {                               // after the slide, tear down
    modal.style.display = 'none';
    reportMaps.forEach(m => { try { m.remove(); } catch (e) {} });
    reportMaps = [];
    reportCharts.forEach(c => { try { c.destroy(); } catch (e) {} });
    reportCharts = [];
    document.getElementById('report-scroll').innerHTML = '';
  }, 360);
}

function buildReport() {
  return reportTablePage() + reportMapPage() + reportAnalysisPage() + reportSitesPage();
}

// Render the report straight to a downloaded PDF (no print dialog). Paginated by
// BLOCK, not by fixed slices: every `.pdf-block` is rasterised whole and placed
// on the current page only if it fits — otherwise it starts a fresh page. A block
// taller than a full page is scaled down to fit one page. So nothing (especially
// a site image) is ever cut across a page boundary.
async function downloadReportPDF() {
  const btn = document.getElementById('report-download');
  if (!window.jspdf || !window.html2canvas) { alert('PDF libraries failed to load.'); return; }
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Building PDF…';
  try {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p', 'pt', 'a4');
    const pw = pdf.internal.pageSize.getWidth();
    const ph = pdf.internal.pageSize.getHeight();
    const M = 26;                       // page margin (pt)
    const GAP = 12;                     // vertical gap between blocks (pt)
    const usableW = pw - 2 * M;
    const usableH = ph - 2 * M;

    const blocks = [...document.querySelectorAll('#report-scroll .pdf-block')];
    let y = M;
    let pageStarted = false;            // has anything been drawn on the current page?

    for (const block of blocks) {
      const canvas = await html2canvas(block, { useCORS: true, scale: 2, backgroundColor: '#0b1020', logging: false });
      let w = usableW;
      let h = canvas.height * (w / canvas.width);
      if (h > usableH) {                // block taller than a page → scale to fit one page
        const s = usableH / h;
        h *= s; w *= s;
      }
      if (pageStarted && y + h > ph - M) {   // not enough room left → next page
        pdf.addPage();
        y = M;
        pageStarted = false;
      }
      const x = M + (usableW - w) / 2;       // centre horizontally
      pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', x, y, w, h);
      y += h + GAP;
      pageStarted = true;
    }
    pdf.save('dc-siting-report.pdf');
  } catch (e) {
    alert('PDF build failed: ' + (e.message || e));
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

function reportTablePage() {
  const cap = document.getElementById('in-capacity').value;
  const foot = document.getElementById('in-surface').value;
  const date = new Date().toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' });

  const thead = `<div class="rp-row rp-thead"><span>#</span><span>Node</span>` +
    METRIC_COLS.map(col => `<span>${COLUMNS[col].label}</span>`).join('') + `</div>`;

  const rows = rankedNodes.map((r, i) => {
    const c = coordsById[r.node_id] || {};
    const country = r.country || c.country || '—';
    const cells = METRIC_COLS.map(col =>
      `<span class="rp-cell">${r[col] != null ? COLUMNS[col].fmt(r[col]) : '—'}</span>`).join('');
    return `<div class="rp-row"><span class="rp-rank">${i + 1}</span>` +
      `<span class="rp-node"><b>${r.node_id}</b><i>${country}</i></span>${cells}</div>`;
  }).join('');

  const assumptions = METRIC_COLS.map(col =>
    `<li><span>${COLUMNS[col].label}</span><b>${Math.round((appliedWeights[col] || 0) * 100)}%</b></li>`).join('');

  return `
    <div class="report-page">
      <div class="rp-header pdf-block">
        <div>
          <div class="rp-title">DC Siting Report</div>
          <div class="rp-meta">Top ${rankedNodes.length} ranked European grid sites</div>
        </div>
        <div class="rp-meta rp-meta-right">${cap} MW · ${(+foot).toLocaleString('en-US')} m²<br>${date}</div>
      </div>
      <div class="rp-table pdf-block">${thead}${rows}</div>
      <div class="assumptions pdf-block">
        <div class="as-title">Assumptions — ranking weights</div>
        <ul>${assumptions}</ul>
        <div class="as-note">Sites ranked by a weighted average of normalised congestion, carbon, cost and connectivity scores (lower is better).</div>
      </div>
    </div>`;
}

function reportMapPage() {
  return `
    <div class="report-page">
      <div class="pdf-block">
        <div class="rp-title">Geographic distribution</div>
        <div class="rp-map" id="report-map"></div>
        <div class="rp-cap">All viable grid nodes (grey) with the top ${rankedNodes.length} ranked sites highlighted in amber.</div>
      </div>
    </div>`;
}

function reportAnalysisPage() {
  const w = rankedNodes[0];
  const wc = coordsById[w.node_id] || {};
  const cards = METRIC_COLS.map(col => {
    const val = w[col] != null ? COLUMNS[col].fmt(w[col]) : '—';
    const med = median(allNodes.map(n => n[col]));
    let delta = '';
    if (med != null && med !== 0 && w[col] != null) {
      const pct = (w[col] - med) / Math.abs(med) * 100;
      const good = pct < 0;  // lower = better for all four metrics
      delta = `<span class="sc-delta ${good ? 'good' : 'bad'}">${pct >= 0 ? '+' : ''}${pct.toFixed(0)}% vs median</span>`;
    }
    return `<div class="stat-card"><div class="sc-label">${COLUMNS[col].label}</div><div class="sc-val">${val}</div>${delta}</div>`;
  }).join('');

  return `
    <div class="report-page">
      <div class="pdf-block">
        <div class="rp-title">Analysis</div>
        <div class="rp-sub">#1 pick — ${w.node_id} · ${w.country || wc.country || ''}</div>
        <div class="stat-cards">${cards}</div>
      </div>
      <div class="pdf-block">
        <div class="rp-sub">Cost composition (energy vs land)</div>
        <div class="chart-wrap"><canvas id="chart-cost"></canvas></div>
      </div>
      <div class="pdf-block">
        <div class="rp-sub">Cost vs CO₂ trade-off</div>
        <div class="chart-wrap"><canvas id="chart-scatter"></canvas></div>
      </div>
    </div>`;
}

function reportSitesPage() {
  const blocks = rankedNodes.map((r, i) => {
    const country = r.country || (coordsById[r.node_id] || {}).country || '';
    return `
      <div class="site-block pdf-block">
        <div class="site-title">#${i + 1} ${r.node_id} · ${country}</div>
        <div class="site-img" id="site-img-${r.node_id}"><div class="site-pending">Generating site imagery…</div></div>
        <div class="site-cap" id="site-cap-${r.node_id}"></div>
      </div>`;
  }).join('');
  return `
    <div class="report-page report-sites">
      <div class="pdf-block">
        <div class="rp-title">Recommended build sites</div>
        <div class="rp-cap">CNN land analysis — true-colour satellite with the chosen buildable footprint (amber box) and largest inscribed pad (yellow circle).</div>
      </div>
      ${blocks}
    </div>`;
}

function buildReportMap() {
  const el = document.getElementById('report-map');
  if (!el || !window.L) return;
  const rmap = L.map(el, { zoomControl: false, scrollWheelZoom: false, attributionControl: true });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO', subdomains: 'abcd', maxZoom: 9,
    crossOrigin: true,  // let html2canvas capture tiles into the PDF
  }).addTo(rmap);

  const topIds = new Set(rankedNodes.map(r => r.node_id));
  const lats = [], lngs = [];
  allNodes.forEach(n => {
    const c = coordsById[n.node_id];
    if (!c || c.lat == null) return;
    const hot = topIds.has(n.node_id);
    L.circleMarker([c.lat, c.lng], hot ? HOT : REPORT_GREY).addTo(rmap);
    lats.push(c.lat); lngs.push(c.lng);
  });
  // Frame to the BULK of the nodes (5th–95th percentile per axis), not the raw
  // min/max — a single far-flung node (e.g. the Canary Islands at 28°N) otherwise
  // blows the zoom out so far that mainland Spain/Italy squish into empty ocean.
  const pctBox = vals => {
    const s = [...vals].sort((a, b) => a - b);
    const q = p => s[Math.min(s.length - 1, Math.max(0, Math.round(p * (s.length - 1))))];
    return [q(0.05), q(0.95)];
  };
  if (lats.length) {
    const [la0, la1] = pctBox(lats), [lo0, lo1] = pctBox(lngs);
    rmap.fitBounds([[la0, lo0], [la1, lo1]], { padding: [34, 34], maxZoom: 7 });
  } else {
    rmap.setView([54, 12], 4);
  }
  reportMaps.push(rmap);
  setTimeout(() => rmap.invalidateSize(), 80);
}

function buildReportCharts() {
  if (!window.Chart) return;
  const labels = rankedNodes.map(r => r.node_id);

  // Fixed-size, non-responsive canvases: print's media-query relayout otherwise
  // sends responsive Chart.js into a resize loop that freezes the page.
  const sizeCanvas = el => { el.width = el.parentElement.clientWidth || 700; el.height = 280; };

  const ctxCost = document.getElementById('chart-cost');
  if (ctxCost) {
    sizeCanvas(ctxCost);
    const energy = rankedNodes.map(r => (detailById[r.node_id] || {}).energy_cost_eur || 0);
    const land = rankedNodes.map(r => (detailById[r.node_id] || {}).land_cost_eur || 0);
    reportCharts.push(new Chart(ctxCost, {
      type: 'bar',
      data: { labels, datasets: [
        { label: 'Energy', data: energy, backgroundColor: '#f59e0b' },
        { label: 'Land', data: land, backgroundColor: '#3b82f6' },
      ] },
      options: {
        responsive: false, maintainAspectRatio: false, animation: false,
        scales: {
          x: { stacked: true, ticks: { color: '#8a98b5', maxRotation: 60, minRotation: 60 }, grid: { display: false } },
          y: { stacked: true, ticks: { color: '#8a98b5', callback: v => fmtEur(v) }, grid: { color: 'rgba(255,255,255,0.06)' } },
        },
        plugins: {
          legend: { labels: { color: '#f5f7fb' } },
          tooltip: { callbacks: { label: c => `${c.dataset.label}: ${fmtEur(c.parsed.y)}` } },
        },
      },
    }));
  }

  const ctxSc = document.getElementById('chart-scatter');
  if (ctxSc) {
    sizeCanvas(ctxSc);
    const all = allNodes.map(n => ({ x: n.total_cost_eur, y: n.dc_carbon_tco2_yr }))
      .filter(p => p.x != null && p.y != null);
    const top = rankedNodes.map(n => ({ x: n.total_cost_eur, y: n.dc_carbon_tco2_yr }))
      .filter(p => p.x != null && p.y != null);
    reportCharts.push(new Chart(ctxSc, {
      type: 'scatter',
      data: { datasets: [
        { label: 'All viable nodes', data: all, backgroundColor: 'rgba(100,116,139,0.4)', pointRadius: 2 },
        { label: 'Top 10', data: top, backgroundColor: '#f59e0b', pointRadius: 5 },
      ] },
      options: {
        responsive: false, maintainAspectRatio: false, animation: false,
        scales: {
          x: { title: { display: true, text: 'Total cost', color: '#8a98b5' }, ticks: { color: '#8a98b5', callback: v => fmtEur(v) }, grid: { color: 'rgba(255,255,255,0.06)' } },
          y: { title: { display: true, text: 'CO₂ (tCO₂/yr)', color: '#8a98b5' }, ticks: { color: '#8a98b5', callback: v => fmtNum(v) }, grid: { color: 'rgba(255,255,255,0.06)' } },
        },
        plugins: { legend: { labels: { color: '#f5f7fb' } } },
      },
    }));
  }
}

// Generate site images STRICTLY on export open — one node per request, in rank
// order, generated on the go by the CNN. Each box fills as its node finishes.
// The backend caches per node, so re-opening the report reuses what's done.
// ~3.8 km -> ~388 px composite, under the DW model's 399 px window, so the CNN
// runs a single inference (no 2x2 tiling) — the biggest per-node speedup.
const AOI_KM = 3.8;
let reportImgToken = 0;
async function loadReportSiteImages() {
  const token = ++reportImgToken;  // invalidated if the modal is reopened
  const fill = (id, html) => { const s = document.getElementById(`site-img-${id}`); if (s) s.innerHTML = html; };
  const cap = (id, html) => { const s = document.getElementById(`site-cap-${id}`); if (s) s.innerHTML = html; };

  rankedNodes.forEach(r =>
    fill(r.node_id, `<div class="site-pending"><span class="site-spin"></span>Analysing land around ${r.node_id}…</div>`));

  const CONCURRENCY = 4;  // overlap network-bound fetches across nodes
  let next = 0;
  async function worker() {
    while (next < rankedNodes.length) {
      if (token !== reportImgToken) return;  // a newer open superseded this run
      const r = rankedNodes[next++];
      try {
        const res = await fetch(`${API}/report/site-images`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ node_ids: [r.node_id], aoi_km: AOI_KM }),
        });
        if (token !== reportImgToken) return;
        if (!res.ok) throw new Error(`site-images ${res.status}`);
        const rec = (await res.json())[0] || {};
        if (rec.image_url) {
          fill(r.node_id, `<img src="${API}${rec.image_url}?t=${Date.now()}" alt="${r.node_id} site" crossorigin="anonymous">`);
          const ha = rec.buildable_area_ha != null ? ` · ${fmtNum(rec.buildable_area_ha)} ha buildable` : '';
          cap(r.node_id, `${rec.dominant_buildable_class || 'site'}${ha}`);
        } else if (rec.status === 'not_cached') {
          fill(r.node_id, `<div class="site-pending">No cached site imagery for this node.</div>`);
        } else {
          fill(r.node_id, `<div class="site-pending">No buildable land / imagery for this node.</div>`);
        }
      } catch (e) {
        if (token !== reportImgToken) return;
        fill(r.node_id, `<div class="site-pending">Site imagery unavailable (analysis stage offline).</div>`);
      }
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
}

// ---------- boot ----------
window.addEventListener('DOMContentLoaded', () => {
  initWeights();
  createMap();
  initControls();
  renderLedger();
});
