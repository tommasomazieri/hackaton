'use strict';
/* DC Hound. Stateless client of /api/query, /api/sources and /api/sites/{id}. */

const METRICS = [
  { key: 'congestion_alpha', label: 'Congestion', tone: 'var(--m1)' },
  { key: 'dc_carbon_tco2_yr', label: 'Carbon', tone: 'var(--m2)' },
  { key: 'total_cost_eur', label: 'Cost', tone: 'var(--m3)' },
  { key: 'connectivity_score', label: 'Connectivity', tone: 'var(--m4)' },
];
const MIX = [
  ['coal', 'Coal', '#6b7285'], ['gas', 'Gas', '#b08560'], ['oil', 'Oil', '#8a6450'],
  ['nuclear', 'Nuclear', '#a98bd8'], ['hydro', 'Hydro', '#4f8fc0'], ['wind', 'Wind', '#7fc4d8'],
  ['solar', 'Solar', '#e9c25a'], ['bioenergy', 'Bioenergy', '#6fae6a'], ['other_renewables', 'Other renewables', '#a8d99a'],
];
const PAGE = matchMedia('(max-width: 820px)').matches ? 10 : 25;
const TOP = 10;
const FLAGS_SHOWN = matchMedia('(max-width: 820px)').matches ? 4 : 7;
const DEFAULT_W = 25; // four weights, always summing to 100
const COST_OF_EQUITY = 0.08; // mirrors src/model/02_compute.py, for the explanation only
const BOUNDARY_NOTICE = '© EuroGeographics for the administrative boundaries';
const IMAGERY_NOTE = 'Sentinel-2 composite (Copernicus) with Google Dynamic World land cover, via Microsoft Planetary Computer.';

const $ = (id) => document.getElementById(id);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
const nf = (d) => new Intl.NumberFormat('en-GB', { minimumFractionDigits: d, maximumFractionDigits: d });
const F = { int: nf(0), d1: nf(1), d2: nf(2) };
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (v, f) => (v == null || Number.isNaN(v) ? '—' : f.format(v));
const flagSrc = (iso) => `flags/${iso.toLowerCase()}.svg`;

const FMT = {
  congestion_alpha: (v) => num(v == null ? v : v * 100, F.d1),
  dc_carbon_tco2_yr: (v) => num(v, F.int),
  total_cost_eur: (v) => num(v == null ? v : v / 1e6, F.d2),
  connectivity_score: (v) => num(v, F.d2),
};
function eur(v) {
  if (v == null) return '—';
  const a = Math.abs(v);
  if (a >= 1e6) return `€${F.d2.format(v / 1e6)} M`;
  if (a >= 1e3) return `€${F.d1.format(v / 1e3)} k`;
  return `€${F.int.format(v)}`;
}
function when(ts) {
  if (!ts) return '—';
  return new Date(ts * 1000).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function ago(ts) {
  if (!ts) return 'never';
  const h = (Date.now() / 1000 - ts) / 3600;
  if (h < 1) return `${Math.max(1, Math.round(h * 60))} min ago`;
  if (h < 48) return `${Math.round(h)} h ago`;
  return `${Math.round(h / 24)} days ago`;
}
const haText = (m2) => `${F.d2.format(m2 / 1e4).replace(/\.?0+$/, '')} ha`;

/* ---------------- State ---------------- */

const S = {
  mw: 50,
  m2: 15000,
  weights: Object.fromEntries(METRICS.map((m) => [m.key, DEFAULT_W])),
  universe: [],          // [{iso, n}] countries with ranked regions
  blocked: new Map(),    // iso → reason (countries with no rankable region)
  sel: new Set(),
  nodes: [],
  byId: new Map(),
  prev: new Map(),       // node_id → rank before the last change
  stats: {},
  maxScore: 1,
  mix: {},
  builtAt: null,
  sources: null,
  names: {},             // iso → country name
  selected: null,
  dock: null,            // 'site' | 'sources' | null
  shown: PAGE,
  land: new Map(),       // node_id → {state, data, error, promise}
  locked: new Set(),     // weight keys held fixed while the others move
};

// Locked weights never move. Moving one weight shares what is left among the unlocked others,
// keeping their proportions. Whole numbers that always total 100 (largest remainder).
const freeOthers = (key) => METRICS.filter((m) => m.key !== key && !S.locked.has(m.key));
// the most this weight can take: 100 minus what the locked others hold
const room = (key) => 100 - METRICS.reduce((a, m) => a + (m.key !== key && S.locked.has(m.key) ? S.weights[m.key] : 0), 0);

function setWeight(key, v) {
  const others = freeOthers(key);
  if (!others.length) return; // every other weight is locked: nothing can absorb the change
  v = Math.min(v, room(key));
  const rest = others.reduce((a, m) => a + S.weights[m.key], 0);
  const left = room(key) - v;
  const raw = others.map((m) => (rest > 0 ? (S.weights[m.key] / rest) * left : left / others.length));
  const out = raw.map(Math.floor);
  let spare = left - out.reduce((a, b) => a + b, 0);
  raw.map((r, i) => [r - out[i], i]).sort((a, b) => b[0] - a[0]).forEach(([, i]) => { if (spare-- > 0) out[i] += 1; });
  S.weights[key] = v;
  others.forEach((m, i) => { S.weights[m.key] = out[i]; });
}

function shares() {
  const tot = METRICS.reduce((a, m) => a + S.weights[m.key], 0);
  return Object.fromEntries(METRICS.map((m) => [m.key, tot > 0 ? S.weights[m.key] / tot : 1 / METRICS.length]));
}
const countryName = (iso) => S.names[iso] || iso;
const selectable = () => S.universe.length;
const inUniverse = (iso) => S.universe.some((u) => u.iso === iso);

/* ---------------- Brief and weights ---------------- */

function buildWeights() {
  $('weights').innerHTML = METRICS.map((m) => `
    <div class="setpoint" style="--tone:${m.tone}">
      <label for="w-${m.key}"><i></i>${m.label}</label>
      <output id="wo-${m.key}" for="w-${m.key}"></output>
      <button type="button" class="lock" data-lock="${m.key}" aria-pressed="false" aria-label="Lock ${m.label}"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="7.5" width="10" height="7" rx="1.8"/><path d="M5.5 7.5V5a2.5 2.5 0 0 1 5 0v2.5"/></svg></button>
      <input type="range" id="w-${m.key}" data-key="${m.key}" min="0" max="100" step="1" value="${S.weights[m.key]}">
    </div>`).join('');
  $('weights').addEventListener('input', (e) => {
    const key = e.target.dataset.key;
    if (!key) return;
    setWeight(key, Number(e.target.value));
    syncWeights();
    scheduleQuery(140);
  });
  $('weights').addEventListener('click', (e) => {
    const key = e.target.closest('[data-lock]')?.dataset.lock;
    if (!key) return;
    if (!S.locked.delete(key)) S.locked.add(key);
    syncWeights();
  });
  syncWeights();
}

function syncWeights() {
  const sh = shares();
  for (const m of METRICS) {
    const input = $(`w-${m.key}`);
    input.value = S.weights[m.key];
    input.style.setProperty('--fill', `${S.weights[m.key]}%`);
    $(`wo-${m.key}`).textContent = `${Math.round(sh[m.key] * 100)}%`;
    const locked = S.locked.has(m.key);
    const stuck = !locked && !freeOthers(m.key).length;
    input.disabled = locked || stuck;
    input.style.setProperty('--room', `${locked ? 100 : room(m.key)}%`);
    input.title = stuck ? 'Every other weight is locked. Unlock one to move this.' : '';
    const btn = document.querySelector(`[data-lock="${m.key}"]`);
    btn.setAttribute('aria-pressed', String(locked));
    btn.setAttribute('aria-label', `${locked ? 'Unlock' : 'Lock'} ${m.label}`);
    btn.title = locked ? `${m.label} is held at ${S.weights[m.key]}%. Click to unlock.` : `Hold ${m.label} at ${S.weights[m.key]}% while you move the others`;
  }
  const free = METRICS.filter((m) => !S.locked.has(m.key));
  $('w-hint').textContent = free.length === 1 ? `Everything but ${free[0].label} is locked, so it cannot move. Unlock one more weight.`
    : !free.length ? 'All four weights are locked. Unlock two to change the mix.' : '';
}

function readBrief() {
  const mw = Number($('in-mw').value);
  const m2 = Number($('in-m2').value);
  const okMw = mw > 0 && mw <= 10000;
  const okM2 = m2 >= 100 && m2 <= 1e8;
  $('in-mw').setAttribute('aria-invalid', String(!okMw));
  $('in-m2').setAttribute('aria-invalid', String(!okM2));
  if (okM2) $('in-ha').textContent = haText(m2);
  if (!okMw) return showMsg('IT load must be between 1 and 10,000 MW.', true), false;
  if (!okM2) return showMsg('Footprint must be between 100 and 100,000,000 m².', true), false;
  S.mw = mw;
  S.m2 = m2;
  return true;
}

/* ---------------- Country ledger ---------------- */

function renderLedger() {
  const sel = S.universe.map((u) => u.iso).filter((iso) => S.sel.has(iso));
  const total = selectable();
  const label = !total ? 'Countries' : sel.length === total ? `All ${total} countries` : `${sel.length} of ${total} countries`;
  const shown = sel.slice(0, FLAGS_SHOWN);
  const rest = sel.length - shown.length;
  const open = !!$('ledger-menu');
  $('ledger-row').innerHTML = `
    <span class="ledger-label">${label}</span>
    ${shown.map((iso) => `<button type="button" class="chip" data-drop="${iso}" title="${esc(countryName(iso))}. Click to leave out." aria-label="Leave out ${esc(countryName(iso))}">
      <img src="${flagSrc(iso)}" alt=""><span class="chip-x" aria-hidden="true">×</span></button>`).join('')}
    ${rest > 0 ? `<button type="button" class="chip chip-more" data-menu aria-haspopup="true" aria-expanded="${open}" title="${rest} more included">+${rest}</button>` : ''}
    ${sel.length < total || !total ? `<button type="button" class="chip chip-add" data-menu aria-haspopup="true" aria-expanded="${open}" title="Add a country" aria-label="Choose countries">+</button>` : ''}`;
  for (const b of document.querySelectorAll('#ledger-menu [data-toggle]')) b.setAttribute('aria-checked', String(S.sel.has(b.dataset.toggle)));
}

function renderMenu() {
  const menu = document.createElement('div');
  menu.id = 'ledger-menu';
  menu.className = 'menu';
  menu.setAttribute('role', 'menu');
  const all = [...S.universe.map((u) => u.iso), ...S.blocked.keys()].sort((a, b) => countryName(a).localeCompare(countryName(b)));
  menu.innerHTML = `
    <div class="menu-head"><b>Countries</b><span>
      <button type="button" class="link" data-all>Select all</button>
      <button type="button" class="link" data-none>Clear</button></span></div>
    <div class="menu-list">${all.map((iso) => {
      const u = S.universe.find((x) => x.iso === iso);
      if (!u) {
        return `<button type="button" class="menu-item" role="menuitemcheckbox" aria-checked="false" disabled title="Excluded: ${esc(S.blocked.get(iso))}">
          <img src="${flagSrc(iso)}" alt=""><span>${esc(countryName(iso))}</span><small>excluded</small><i class="tick"></i></button>`;
      }
      return `<button type="button" class="menu-item" role="menuitemcheckbox" data-toggle="${iso}" aria-checked="${S.sel.has(iso)}">
        <img src="${flagSrc(iso)}" alt=""><span>${esc(countryName(iso))}</span><small>${u.n} regions</small><i class="tick"></i></button>`;
    }).join('')}</div>
    <p class="menu-foot">Click a country on the map to toggle it too.</p>`;
  $('ledger').appendChild(menu);
}

function toggleMenu(force) {
  const open = force ?? !$('ledger-menu');
  $('ledger-menu')?.remove();
  if (open) renderMenu();
  for (const b of $('ledger').querySelectorAll('[data-menu]')) b.setAttribute('aria-expanded', String(open));
  if (open) $('ledger-menu').querySelector('.menu-item:not(:disabled)')?.focus();
}

function syncCountries() {
  renderLedger();
  styleCountries();
  styleDots();
}

function toggleCountry(iso) {
  if (!inUniverse(iso)) return;
  S.sel.has(iso) ? S.sel.delete(iso) : S.sel.add(iso);
  syncCountries();
  scheduleQuery(200);
}

/* ---------------- Query ---------------- */

let qSeq = 0;
let qTimer = null;
let qCtl = null;

function scheduleQuery(delay = 250) {
  clearTimeout(qTimer);
  qTimer = setTimeout(runQuery, delay);
}

async function runQuery() {
  clearTimeout(qTimer);
  if (!readBrief()) return;
  if (selectable() && S.sel.size === 0) return showEmpty('No countries selected. Add one from the list at the top left of the map.');
  const seq = ++qSeq;
  qCtl?.abort();
  qCtl = new AbortController();
  const all = !selectable() || S.sel.size === selectable();
  const body = { capacity_mw: S.mw, surface_m2: S.m2, weights: { ...S.weights }, countries: all ? null : [...S.sel] };
  $('btn-go').classList.add('is-busy');
  let res;
  let data;
  try {
    res = await fetch('/api/query', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: qCtl.signal,
    });
    data = await res.json();
  } catch (err) {
    if (err.name === 'AbortError') return;
    $('btn-go').classList.remove('is-busy');
    return showMsg('The server did not answer. Check that it is running, then change any input to retry.', true);
  }
  if (seq !== qSeq) return;
  $('btn-go').classList.remove('is-busy');
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'The server rejected these inputs.';
    if (res.status === 503) {
      showMsg(`${detail} Retrying in 15 s.`, true);
      return scheduleQuery(15000);
    }
    return showEmpty(detail);
  }
  apply(data, all);
}

function apply(data, all) {
  S.prev = new Map(S.nodes.map((n) => [n.node_id, n.rank]));
  S.nodes = data.nodes;
  S.byId = new Map(S.nodes.map((n) => [n.node_id, n]));
  S.mix = data.mix || {};
  S.builtAt = data.data_built_at;
  if (!selectable() && all) initUniverse();
  computeStats();
  showMsg('');
  renderStatus();
  renderRows();
  renderPins();
  styleDots();
  if (S.dock === 'site') S.byId.has(S.selected) ? renderSite() : closeDock();
  if (!$('report').hidden) renderReport();
}

function computeStats() {
  S.stats = {};
  for (const m of METRICS) {
    const vals = S.nodes.map((n) => n[m.key]).filter((v) => v != null).sort((a, b) => a - b);
    S.stats[m.key] = { min: vals[0] ?? 0, max: vals[vals.length - 1] ?? 1, median: vals[Math.floor(vals.length / 2)] ?? 0, sorted: vals };
  }
  const sh = shares();
  S.maxScore = Math.max(1e-9, ...S.nodes.map((n) => score(n, sh)));
}

function score(n, sh) {
  return METRICS.reduce((a, m) => a + sh[m.key] * (n[`norm_${m.key}`] ?? 0), 0);
}

/* Share of regions in this query that do worse than v (lower is better). */
function betterThan(key, v) {
  const a = S.stats[key].sorted;
  let lo = 0;
  let hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] <= v) lo = mid + 1; else hi = mid; }
  return a.length > 1 ? (a.length - lo) / (a.length - 1) : 0;
}

/* ---------------- Header status ---------------- */

async function loadSources() {
  try {
    const r = await fetch('/api/sources');
    if (r.ok) S.sources = await r.json();
  } catch { /* the header shows what the query returned */ }
  if (!S.sources) return;
  for (const e of S.sources.excluded || []) {
    if (!S.blocked.has(e.country) && !inUniverse(e.country)) S.blocked.set(e.country, e.reason);
  }
  renderStatus();
  if (S.dock === 'sources') renderSources();
}

function feedFaults() {
  const out = [];
  for (const src of S.sources?.sources || []) {
    const bad = (src.parts || []).filter((p) => p.status !== 'fresh');
    if (bad.length) out.push(...bad.map((p) => `${src.key}/${p.key}`));
    else if (!src.parts && src.status !== 'fresh') out.push(src.key);
  }
  return out;
}

function renderStatus() {
  const built = S.builtAt ?? S.sources?.built_at;
  $('st-built').textContent = built ? `Data built ${when(built)}` : '';
  const excluded = S.sources?.excluded?.length || 0;
  const faults = feedFaults().length;
  const parts = [];
  if (excluded) parts.push(`${excluded} regions excluded`);
  if (faults) parts.push(`${faults} feed ${faults === 1 ? 'fault' : 'faults'}`);
  $('st-faults').hidden = !parts.length;
  $('st-faults').textContent = parts.join(' · ');
}

/* ---------------- Ranked sites ---------------- */

function gauge(m, v) {
  const s = S.stats[m.key];
  if (v == null || !s) return '';
  const span = s.max - s.min || 1;
  const p = (x) => `${(((x - s.min) / span) * 100).toFixed(1)}%`;
  return `<div class="gauge" style="color:${m.tone}" aria-hidden="true"><span class="g-fill" style="width:${p(v)}"></span><span class="g-med" style="left:${p(s.median)}"></span></div>`;
}

function whyBar(n) {
  const sh = shares();
  const segs = METRICS.map((m) => {
    const norm = n[`norm_${m.key}`] ?? 0;
    const w = (sh[m.key] * norm) / S.maxScore;
    return `<i style="width:${(w * 100).toFixed(2)}%;background:${m.tone}" title="${m.label}: weight ${Math.round(sh[m.key] * 100)}% × normalised ${F.d2.format(norm)}"></i>`;
  }).join('');
  return `<div class="why" role="img" aria-label="Score make-up; full width is the weakest region">${segs}</div>`;
}

function movedHtml(n) {
  if (!S.prev.size) return '';
  const was = S.prev.get(n.node_id);
  if (was === n.rank) return '';
  if (was == null) return '<span class="rank-was new">new</span>';
  return was > n.rank
    ? `<span class="rank-was up" title="Up from ${was}">▲ ${was}</span>`
    : `<span class="rank-was down" title="Down from ${was}">▼ ${was}</span>`;
}

function rowHtml(n) {
  const noSubs = n.infra_data_quality && n.infra_data_quality !== 'ok' ? '<span class="flag">no substation data</span>' : '';
  const inline = METRICS.map((m) => `<span>${m.label}<b>${FMT[m.key](n[m.key])}</b></span>`).join('');
  return `
    <td class="c-rank"><span class="rank-no">${n.rank}</span>${movedHtml(n)}</td>
    <td><span class="region-name">${esc(n.name || n.node_id)}</span><span class="region-code">${n.node_id} · ${esc(countryName(n.country))}${noSubs}</span>${whyBar(n)}<div class="metrics-inline">${inline}</div></td>
    ${METRICS.map((m) => `<td class="n"><span class="m-val">${FMT[m.key](n[m.key])}</span></td>`).join('')}`;
}

function renderRows() {
  const tbody = $('rows');
  const before = new Map([...tbody.children].map((tr) => [tr.dataset.id, tr.getBoundingClientRect().top]));
  const existing = new Map([...tbody.children].map((tr) => [tr.dataset.id, tr]));
  const frag = document.createDocumentFragment();
  for (const n of S.nodes.slice(0, S.shown)) {
    let tr = existing.get(n.node_id);
    if (tr) existing.delete(n.node_id);
    else {
      tr = document.createElement('tr');
      tr.dataset.id = n.node_id;
      tr.tabIndex = 0;
    }
    tr.innerHTML = rowHtml(n);
    tr.classList.toggle('is-top', n.rank <= TOP);
    tr.classList.toggle('is-selected', n.node_id === S.selected);
    tr.setAttribute('aria-label', `Rank ${n.rank}, ${n.name || n.node_id}, ${countryName(n.country)}`);
    frag.appendChild(tr);
  }
  existing.forEach((tr) => tr.remove());
  tbody.appendChild(frag);
  $('more').hidden = S.shown >= S.nodes.length;
  const total = S.universe.reduce((a, u) => a + u.n, 0);
  const count = S.nodes.length === total ? F.int.format(total) : `${F.int.format(S.nodes.length)} of ${F.int.format(total)}`;
  $('rank-sub').textContent = `${count} regions (NUTS 3). Lower is better on all four.`;
  if (reduceMotion.matches || !before.size) return;
  flip(tbody, before);
}

/* FLIP: rows slide from where they were to where they now are. */
function flip(tbody, before) {
  const moved = [];
  for (const tr of tbody.children) {
    const top = before.get(tr.dataset.id);
    if (top == null) {
      tr.classList.remove('is-new');
      void tr.offsetWidth;
      tr.classList.add('is-new');
      continue;
    }
    const dy = top - tr.getBoundingClientRect().top;
    if (Math.abs(dy) < 1) continue;
    tr.style.transition = 'none';
    tr.style.transform = `translateY(${dy}px)`;
    moved.push(tr);
  }
  if (!moved.length) return;
  void tbody.offsetHeight;
  for (const tr of moved) {
    tr.style.transition = 'transform 240ms var(--ease)';
    tr.style.transform = '';
  }
}

function showMsg(text, fault = false) {
  $('rank-msg').textContent = text;
  $('rank-msg').className = fault ? 'msg-fault' : '';
}

function showEmpty(text) {
  S.nodes = [];
  S.byId = new Map();
  $('rows').innerHTML = '';
  $('more').hidden = true;
  $('rank-sub').textContent = 'No regions in this selection.';
  renderPins();
  styleDots();
  renderStatus();
  closeDock();
  showMsg(text, true);
}

/* ---------------- Map ---------------- */

// The basemap is the GISCO country file itself: no tile service, no key.
const EUROPE = [[33, -28], [72, 45]]; // pan limit, same box as the original map
// Canvas drawn 60% past each edge, so pans and zoom-outs reveal map already drawn, not blank.
const renderer = L.canvas({ padding: 0.6 });
// No zoom animation: it shrinks the old canvas and shows blank edges until redrawn. Zoom snaps to the redrawn map.
// keyboard: false stops Leaflet focusing the map on click (a stray focus ring); the ranked list is the keyboard path.
const map = L.map('map', { renderer, zoomSnap: 0.25, maxZoom: 9, zoomControl: false, zoomAnimation: false, keyboard: false, maxBounds: EUROPE, maxBoundsViscosity: 1 });
L.control.zoom({ position: 'bottomright' }).addTo(map);
map.attributionControl.setPrefix(false);
map.attributionControl.addAttribution(BOUNDARY_NOTICE);
map.fitBounds([[35, -11], [71, 32]], { paddingTopLeft: [0, 40] });
map.setMinZoom(map.getZoom()); // no zooming out past Europe
// A long drag can leave the pre-drawn area: redraw right then, not on mouse release.
map.on('move', () => {
  const view = L.bounds(map.containerPointToLayerPoint([0, 0]), map.containerPointToLayerPoint(map.getSize()));
  if (renderer._bounds && !renderer._bounds.contains(view)) renderer._update();
});

let countryLayer = null;
const dots = new Map();
const pins = L.layerGroup().addTo(map);
let ring = null;

const DOT_ON = { radius: 3, stroke: false, fillColor: '#8a93a8', fillOpacity: 0.7 };
const DOT_OFF = { radius: 2, stroke: false, fillColor: '#343b4a', fillOpacity: 0.6 };
// dots grow with zoom so dense regions (DE, Benelux) stay readable when zoomed out
function sizeDots() {
  const z = map.getZoom();
  DOT_ON.radius = z < 4 ? 2 : z < 5 ? 2.5 : z < 6 ? 3 : 4;
  DOT_OFF.radius = DOT_ON.radius * 0.7;
  styleDots();
}
map.on('zoomend', sizeDots);
const DOT_HOT = { radius: 7, stroke: true, color: '#0c0f16', weight: 2, fillColor: '#e3a651', fillOpacity: 1 };

const LAND_OUT = { color: '#1d222d', opacity: 1, weight: 0.6, fillColor: '#12151d', fillOpacity: 1 };
const LAND_ON = { color: '#3a4354', opacity: 1, weight: 0.8, fillColor: '#1a1f2b', fillOpacity: 1 };
const LAND_OFF = { color: '#1d222d', opacity: 1, weight: 0.6, fillColor: '#0e1118', fillOpacity: 1 };

function countryStyle(f) {
  const iso = f.properties.iso;
  if (!inUniverse(iso)) return LAND_OUT;
  return S.sel.has(iso) ? LAND_ON : LAND_OFF;
}

function styleCountries() {
  countryLayer?.setStyle(countryStyle);
}

function drawCountries(geo) {
  for (const f of geo.features) S.names[f.properties.iso] = f.properties.name;
  countryLayer = L.geoJSON(geo, { style: countryStyle }).addTo(map).bringToBack();
  if (!selectable()) return;
  // the ranking arrived first: wire the countries now
  S.universe.sort((a, b) => countryName(a.iso).localeCompare(countryName(b.iso)));
  wireCountries();
  syncCountries();
  renderRows(); // rows were drawn with ISO codes; now they get country names
}

function wireCountries() {
  countryLayer?.eachLayer((layer) => {
    const iso = layer.feature.properties.iso;
    if (!inUniverse(iso)) {
      layer.options.interactive = false;
      return;
    }
    layer.bindTooltip(() => `<b>${esc(countryName(iso))}</b><small>${S.sel.has(iso) ? 'Included' : 'Left out'}. Click to toggle.</small>`, { sticky: true, className: 'tip' });
    layer.on('click', () => toggleCountry(iso));
  });
}

function initUniverse() {
  const counts = new Map();
  for (const n of S.nodes) {
    counts.set(n.country, (counts.get(n.country) || 0) + 1);
    const dot = L.circleMarker([n.lat, n.lng], DOT_ON);
    dot.bindTooltip(() => dotTip(n.node_id), { direction: 'top', offset: [0, -6], className: 'tip' });
    dot.on('click', () => select(n.node_id));
    dot.addTo(map);
    dots.set(n.node_id, dot);
  }
  S.universe = [...counts].map(([iso, n]) => ({ iso, n })).sort((a, b) => countryName(a.iso).localeCompare(countryName(b.iso)));
  for (const u of S.universe) S.blocked.delete(u.iso);
  S.sel = new Set(S.universe.map((u) => u.iso));
  wireCountries();
  syncCountries();
  sizeDots();
}

function dotTip(id) {
  const n = S.byId.get(id);
  if (!n) return `<b>${esc(id)}</b><small>Country left out</small>`;
  return `<b>${esc(n.name || id)}</b><small>${id} · ${esc(countryName(n.country))} · rank ${F.int.format(n.rank)}</small>
    <dl>${METRICS.map((m) => `<dt>${m.label}</dt><dd>${FMT[m.key](n[m.key])}</dd>`).join('')}</dl>`;
}

function styleDots() {
  for (const [id, dot] of dots) dot.setStyle(S.byId.has(id) ? DOT_ON : DOT_OFF);
}

function renderPins() {
  pins.clearLayers();
  for (const n of S.nodes.slice(0, TOP)) {
    const icon = L.divIcon({
      className: '',
      html: `<span class="pin${n.node_id === S.selected ? ' is-selected' : ''}" data-id="${n.node_id}">${n.rank}</span>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });
    const m = L.marker([n.lat, n.lng], { icon, title: `${n.rank}. ${n.name || n.node_id}`, keyboard: true, zIndexOffset: 1000 - n.rank });
    m.on('click', () => select(n.node_id));
    m.on('mouseover', () => hot(n.node_id, true));
    m.on('mouseout', () => hot(n.node_id, false));
    pins.addLayer(m);
  }
  drawRing();
}

function drawRing() {
  ring?.remove();
  ring = null;
  const n = S.byId.get(S.selected);
  if (!n || n.rank <= TOP) return;
  ring = L.circleMarker([n.lat, n.lng], { radius: 10, color: '#e3a651', weight: 2, fill: false, interactive: false }).addTo(map);
}

function hot(id, on) {
  document.querySelector(`#rows tr[data-id="${id}"]`)?.classList.toggle('is-hot', on);
  const pin = document.querySelector(`.pin[data-id="${id}"]`);
  if (pin) return pin.classList.toggle('is-hot', on);
  const dot = dots.get(id);
  if (dot && S.byId.has(id)) {
    dot.setStyle(on ? DOT_HOT : DOT_ON);
    if (on) dot.bringToFront();
  }
}

/* ---------------- Dock ---------------- */

const CLOSE = '<button type="button" class="dock-close" data-close aria-label="Close panel"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M1 1l10 10M11 1L1 11"/></svg></button>';

function openDock(mode, html) {
  const fresh = S.dock !== mode;
  S.dock = mode;
  $('dock').innerHTML = html;
  $('dock').hidden = false;
  if (fresh) $('dock').scrollTop = 0;
  $('btn-sources').setAttribute('aria-pressed', String(mode === 'sources'));
}

function closeDock() {
  const had = S.selected;
  S.dock = null;
  S.selected = null;
  $('dock').hidden = true;
  $('btn-sources').setAttribute('aria-pressed', 'false');
  if (had) markSelection();
}

function select(id) {
  if (!S.byId.has(id)) return;
  const changed = S.selected !== id;
  S.selected = id;
  renderSite();
  if (changed) $('dock').scrollTop = 0;
  markSelection();
  const n = S.byId.get(id);
  const wide = innerWidth > 820;
  map.panInside([n.lat, n.lng], { paddingTopLeft: [60, 80], paddingBottomRight: [wide ? 430 : 40, 60] });
  document.querySelector(`#rows tr[data-id="${id}"]`)?.scrollIntoView({ block: 'nearest' });
}

function markSelection() {
  for (const tr of $('rows').children) tr.classList.toggle('is-selected', tr.dataset.id === S.selected);
  for (const p of document.querySelectorAll('.pin')) p.classList.toggle('is-selected', p.dataset.id === S.selected);
  drawRing();
}

function readout(m, value, unit, v) {
  const pct = Math.round(betterThan(m.key, v) * 100);
  return `<div class="readout">
    <span class="r-label"><i style="background:${m.tone}"></i>${m.label}</span>
    <span class="r-value">${value}<small>${unit}</small></span>
    ${gauge(m, v)}
    <span class="r-note">Better than <b>${pct}%</b> of regions</span>
  </div>`;
}

function priceLicence(zone) {
  const src = S.sources?.sources?.find((s) => s.key === 'price');
  return src?.parts?.find((p) => p.key === zone)?.license || null;
}

function renderSite() {
  const n = S.byId.get(S.selected);
  if (!n) return;
  const [mC, mCO2, mCost, mConn] = METRICS;
  const ha = S.m2 / 1e4;
  const lic = priceLicence(n.price_zone);
  const licHtml = !lic ? '—' : /internal/i.test(lic) ? `<span class="flag">${esc(lic)}</span>` : esc(lic);
  const noSubs = n.infra_data_quality && n.infra_data_quality !== 'ok';
  const mix = S.mix[n.country];
  openDock('site', `
    <div class="dock-head">
      <span class="rank-no${n.rank <= TOP ? ' is-top-plate' : ''}">${n.rank}</span>
      <div><h3>${esc(n.name || n.node_id)}</h3><p>${n.node_id} · ${esc(countryName(n.country))}. NUTS 3 region, scored at its centre point.</p></div>
      ${CLOSE}
    </div>
    <section class="dock-sec">
      <div class="readouts">
        ${readout(mC, FMT.congestion_alpha(n.congestion_alpha), '% of hours', n.congestion_alpha)}
        ${readout(mCO2, FMT.dc_carbon_tco2_yr(n.dc_carbon_tco2_yr), 't CO₂/yr', n.dc_carbon_tco2_yr)}
        ${readout(mCost, eur(n.total_cost_eur), '', n.total_cost_eur)}
        ${readout(mConn, FMT.connectivity_score(n.connectivity_score), 'of 1, 0 best', n.connectivity_score)}
      </div>
      <p class="readout-note">Bars run from the best to the worst region in this query; the tick is the median.
        Congestion is the chance that demand plus this load exceeds estimated capacity in an hour, a national proxy rather than a grid study.
        Carbon is ${num(n.carbon_intensity_elec, F.int)} g CO₂/kWh (country average) × ${num(S.mw, F.int)} MW × 8,760 h.
        Connectivity is half distance to a high-voltage substation, half internet exchanges nearby.</p>
    </section>
    <section class="dock-sec">
      <h4>Cost build-up</h4>
      <dl class="kv">
        <dt>Day-ahead price, zone ${esc(n.price_zone)}</dt><dd>€${num(n.energy_price_eur_mwh, F.d2)}/MWh</dd>
        <dt>Energy per year</dt><dd>${eur(n.energy_cost_eur)}</dd>
        <dt>Farmland price</dt><dd>€${num(n.land_price_eur_ha, F.int)}/ha</dd>
        <dt>Land term (price × ${F.d2.format(ha).replace(/\.?0+$/, '')} ha ÷ ${COST_OF_EQUITY * 100}%)</dt><dd>${eur(n.land_cost_eur)}</dd>
        <dt>Price data licence</dt><dd class="txt">${licHtml}</dd>
      </dl>
    </section>
    <section class="dock-sec">
      <h4>Grid and network</h4>
      <dl class="kv">
        <dt>Nearest substation, 110 kV or more</dt><dd>${noSubs ? '<span class="flag">no substation data</span>' : `${num(n.dist_to_hv_substation_km, F.d1)} km`}</dd>
        <dt>Internet exchanges within 50 km</dt><dd>${num(n.ixp_count_50km, F.int)}</dd>
        <dt>Nearest internet exchange</dt><dd>${num(n.dist_to_nearest_ixp_km, F.d1)} km</dd>
        <dt>Capacity share (national ÷ regions)</dt><dd>${num(n.capacity_mw, F.int)} MW</dd>
        <dt>Mean demand share</dt><dd>${num(n.consumption_mean_mw, F.int)} MW</dd>
        <dt>Region area</dt><dd>${num(n.area_km2, F.int)} km²</dd>
      </dl>
    </section>
    ${mix ? `<section class="dock-sec">
      <h4>${esc(countryName(n.country))} generation mix, ${mix.year}</h4>
      ${mixBar(mix)}
      <p class="caption">Share of electricity generation. Our World in Data.</p>
    </section>` : ''}
    <section class="dock-sec" id="land-sec"></section>`);
  renderLand();
}

function mixBar(mix) {
  const segs = MIX.filter(([k]) => (mix[k] || 0) > 0);
  return `<div class="mix" role="img" aria-label="${segs.map(([k, l]) => `${l} ${F.int.format(mix[k])}%`).join(', ')}">
    ${segs.map(([k, l, c]) => `<i style="width:${mix[k]}%;background:${c}" title="${l} ${F.d1.format(mix[k])}%"></i>`).join('')}
  </div>
  <div class="mix-legend">${segs.filter(([k]) => mix[k] >= 1).map(([k, l, c]) => `<span><i style="background:${c}"></i>${l} ${F.int.format(mix[k])}%</span>`).join('')}</div>`;
}

function landHtml(id, e) {
  const h = '<h4>Buildable land</h4>';
  if (!e) {
    return `${h}<p>Classifies a 3.8 km square around the region's centre point from satellite imagery. The first run for a region takes about 30 seconds.</p>
      <p><button type="button" class="btn" data-land="${id}">Analyse land</button></p>`;
  }
  if (e.state === 'loading') return `${h}<p class="land-busy" role="status"><i class="spin"></i>Fetching the Sentinel-2 composite, then classifying land cover…</p>`;
  if (e.state === 'error') {
    return `${h}<p class="flag">${esc(e.error)}</p><p><button type="button" class="btn" data-land="${id}">Try again</button></p>`;
  }
  const d = e.data;
  if (d.status !== 'ok') {
    return `${h}<p>${d.status === 'no_buildable_land' ? 'No buildable land found in the 3.8 km square.' : esc(d.status)}</p>`;
  }
  return `${h}
    ${d.image_url ? `<img class="land-img" src="${d.image_url}" alt="Satellite image of the 3.8 km square around ${esc(id)}, with the largest buildable patch marked">` : ''}
    <dl class="kv">
      <dt>Buildable area in the square</dt><dd>${num(d.buildable_area_ha, F.d1)} ha</dd>
      <dt>Mostly</dt><dd class="txt">${esc(String(d.dominant_buildable_class || '—').replaceAll('_', ' '))}</dd>
      <dt>Largest patch</dt><dd>${num(d.chosen_patch?.area_ha, F.d1)} ha</dd>
    </dl>
    <p class="caption">${IMAGERY_NOTE}</p>`;
}

function renderLand() {
  const sec = $('land-sec');
  if (sec && S.selected) sec.innerHTML = landHtml(S.selected, S.land.get(S.selected));
}

function landFetch(id) {
  const cur = S.land.get(id);
  if (cur && cur.state !== 'error') return cur.promise;
  const e = { state: 'loading' };
  S.land.set(id, e);
  e.promise = fetch(`/api/sites/${encodeURIComponent(id)}`)
    .then(async (r) => {
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : `Land analysis failed (${r.status}).`);
      Object.assign(e, { state: 'ok', data: d });
    })
    .catch((err) => Object.assign(e, { state: 'error', error: err.message || 'Land analysis failed.' }))
    .finally(() => { if (S.selected === id) renderLand(); });
  if (S.selected === id) renderLand();
  return e.promise;
}

function renderSources() {
  const s = S.sources;
  const feeds = (s?.sources || []).map((src) => {
    const bad = (src.parts || []).filter((p) => p.status !== 'fresh');
    let state = '';
    if (src.parts && bad.length) state = `<p class="flag">${bad.length} of ${src.parts.length} failed: ${bad.map((p) => esc(p.key)).join(', ')}</p>`;
    else if (!src.parts && src.status !== 'fresh') state = `<p class="flag">${esc(src.status)}${src.error ? `: ${esc(src.error)}` : ''}</p>`;
    const lic = [...new Set((src.parts || []).map((p) => p.license).filter(Boolean))];
    const licHtml = lic.length ? `<p>Licences: ${lic.map((l) => (/internal/i.test(l) ? `<span class="flag">${esc(l)}</span>` : esc(l))).join('; ')}.</p>` : '';
    return `<div class="src">
      <p class="src-what">${esc(src.what)}</p>
      <p>${esc(src.provider)}. Updated ${ago(src.fetched_at)}, refreshed every ${src.ttl_hours >= 48 ? `${Math.round(src.ttl_hours / 24)} days` : `${Math.round(src.ttl_hours)} h`}. <a href="${esc(src.terms)}" target="_blank" rel="noopener">Terms</a></p>
      ${licHtml}${state}
    </div>`;
  }).join('');
  const excluded = (s?.excluded || []).map((e) => `<dt>${esc(e.node_id)} · ${esc(countryName(e.country))}</dt><dd class="flag">${esc(e.reason)}</dd>`).join('');
  openDock('sources', `
    <div class="dock-head plain">
      <div><h3>Sources and limits</h3><p>Data built ${when(S.builtAt ?? s?.built_at)}. Every figure comes from one of these feeds.</p></div>
      ${CLOSE}
    </div>
    <section class="dock-sec"><h4>Feeds</h4>${feeds || '<p>Source list unavailable.</p>'}</section>
    ${excluded ? `<section class="dock-sec"><h4>Excluded regions</h4><dl class="kv">${excluded}</dl></section>` : ''}
    <section class="dock-sec"><h4>What the ranking does not cover</h4>${limitsHtml()}</section>`);
}

function limitsHtml() {
  return `<ul class="limits">
    <li>Congestion is a national proxy (annual demand against estimated capacity, split evenly across regions). There is no power-flow study, connection queue or lead time.</li>
    <li>Carbon uses the country's average grid intensity, not hourly or contracted supply.</li>
    <li>Land price is farmland (Eurostat, NUTS 2), not industrial land. The land term is price × area ÷ ${COST_OF_EQUITY * 100}% and is added to one year of energy cost.</li>
    <li>Connectivity measures distance to mapped substations and internet exchanges, not their spare capacity.</li>
    <li>Permitting, grid-connection moratoria, waste-heat duties and water are not scored.</li>
    <li>Some day-ahead prices are licensed for private and internal use only. Eurostat GISCO boundaries are licensed for non-commercial use.</li>
  </ul>`;
}

/* ---------------- Report (export) ---------------- */

let landRun = null;

function renderReport() {
  const top = S.nodes.slice(0, TOP);
  const sh = shares();
  const all = S.sel.size === selectable();
  const countries = all ? `All ${selectable()}` : [...S.sel].map(countryName).sort().join(', ');
  const med = (k) => S.stats[k]?.median;
  const landDone = top.filter((n) => S.land.get(n.node_id)?.state === 'ok' && S.land.get(n.node_id).data.status === 'ok');
  const running = landRun !== null;
  $('report').innerHTML = `
    <div class="report-bar">
      <button type="button" class="btn" data-report-close>← Back to map</button>
      <button type="button" class="btn" data-report-land ${running || !top.length ? 'disabled' : ''}>${running ? `Analysing land: ${landRun} of ${top.length}` : 'Add land imagery for the top 10'}</button>
      <button type="button" class="btn btn-amber" data-report-print>Print or save as PDF</button>
    </div>
    <div class="sheet">
      <p class="sheet-brand">DC HOUND</p>
      <h1>Data-centre site shortlist</h1>
      <p class="lede">The ${top.length} best of ${F.int.format(S.nodes.length)} EU regions (NUTS 3) for a ${F.int.format(S.mw)} MW, ${haText(S.m2)} data centre, ranked on grid congestion, carbon, cost and connectivity. Lower is better on all four.</p>
      <dl class="meta">
        <div><dt>IT load</dt><dd>${F.int.format(S.mw)} MW</dd></div>
        <div><dt>Footprint</dt><dd>${F.int.format(S.m2)} m²</dd></div>
        <div><dt>Countries</dt><dd>${esc(countries)}</dd></div>
        <div><dt>Weights</dt><dd>${METRICS.map((m) => `${m.label} ${Math.round(sh[m.key] * 100)}%`).join(', ')}</dd></div>
        <div><dt>Generated</dt><dd>${when(Date.now() / 1000)}</dd></div>
        <div><dt>Data built</dt><dd>${when(S.builtAt)}</dd></div>
      </dl>

      <h2>Shortlist</h2>
      <div class="t-wide"><table>
        <thead><tr>
          <th>Rank</th><th>Region</th>
          <th class="n">Congestion<span>% of hours</span></th>
          <th class="n">Carbon<span>t CO₂/yr</span></th>
          <th class="n">Energy<span>€ M per year</span></th>
          <th class="n">Land term<span>€ k</span></th>
          <th class="n">Connectivity<span>0 best</span></th>
          <th class="n">Substation<span>km</span></th>
          <th class="n">Exchanges<span>within 50 km</span></th>
        </tr></thead>
        <tbody>
          ${top.map((n) => `<tr>
            <td><span class="rank-no">${n.rank}</span></td>
            <td>${esc(n.name || n.node_id)}<br><span class="sub">${n.node_id} · ${esc(countryName(n.country))}</span></td>
            <td class="n">${FMT.congestion_alpha(n.congestion_alpha)}</td>
            <td class="n">${FMT.dc_carbon_tco2_yr(n.dc_carbon_tco2_yr)}</td>
            <td class="n">${num(n.energy_cost_eur / 1e6, F.d2)}</td>
            <td class="n">${num(n.land_cost_eur / 1e3, F.d1)}</td>
            <td class="n">${FMT.connectivity_score(n.connectivity_score)}</td>
            <td class="n">${n.infra_data_quality === 'ok' ? num(n.dist_to_hv_substation_km, F.d1) : '<span class="flag">no data</span>'}</td>
            <td class="n">${num(n.ixp_count_50km, F.int)}</td>
          </tr>`).join('')}
          <tr class="median">
            <td></td><td>Median of all ${F.int.format(S.nodes.length)} regions</td>
            <td class="n">${FMT.congestion_alpha(med('congestion_alpha'))}</td>
            <td class="n">${FMT.dc_carbon_tco2_yr(med('dc_carbon_tco2_yr'))}</td>
            <td class="n" colspan="2">${FMT.total_cost_eur(med('total_cost_eur'))} total</td>
            <td class="n">${FMT.connectivity_score(med('connectivity_score'))}</td>
            <td></td><td></td>
          </tr>
        </tbody>
      </table></div>

      <h2>Where they are</h2>
      ${reportMap(top)}
      <p class="fig-note">Small dots are all regions ranked. Numbered markers are the shortlist. ${BOUNDARY_NOTICE}.</p>

      <h2>Cost against carbon</h2>
      ${scatter(top)}
      <p class="fig-note">Each dot is one region. Lower and further left is better on both.</p>

      ${landDone.length ? `<h2>Buildable land</h2>
      <div class="figs">${landDone.map((n) => {
        const d = S.land.get(n.node_id).data;
        return `<figure>
          ${d.image_url ? `<img src="${d.image_url}" alt="Satellite image around ${esc(n.name || n.node_id)}">` : ''}
          <figcaption><b>${n.rank}. ${esc(n.name || n.node_id)}</b>. Buildable ${num(d.buildable_area_ha, F.d1)} ha, mostly ${esc(String(d.dominant_buildable_class || '').replaceAll('_', ' '))}; largest patch ${num(d.chosen_patch?.area_ha, F.d1)} ha. ${IMAGERY_NOTE}</figcaption>
        </figure>`;
      }).join('')}</div>` : ''}

      <h2>How the ranking works</h2>
      <p>Each readout is divided by its largest value across the regions ranked, then weighted by the shares above and summed. The ranking uses that sum; it is not shown as a score.</p>
      <p style="margin:10px 0 6px">What it does not cover:</p>
      ${limitsHtml()}

      <h2>Sources</h2>
      <ul>${(S.sources?.sources || []).map((src) => `<li>${esc(src.what)}: ${esc(src.provider)}, fetched ${when(src.fetched_at)}. Terms: ${esc(src.terms)}</li>`).join('')}
        <li>${BOUNDARY_NOTICE}.</li></ul>
    </div>`;
}

function proj([lng, lat]) {
  return [(lng - 10) * Math.cos((52 * Math.PI) / 180), -lat];
}

function reportMap(top) {
  const [x0, y0] = proj([-10.5, 71]);
  const [x1, y1] = proj([31.5, 34.5]);
  const W = 760;
  const k = W / (x1 - x0);
  const H = Math.round((y1 - y0) * k);
  const P = (ll) => { const [x, y] = proj(ll); return [((x - x0) * k).toFixed(1), ((y - y0) * k).toFixed(1)]; };
  const ringPath = (r) => `M${r.map((c) => P(c).join(',')).join('L')}Z`;
  const paths = (countryLayer ? countryLayer.toGeoJSON().features : []).map((f) => {
    const g = f.geometry;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
    const on = inUniverse(f.properties.iso) && S.sel.has(f.properties.iso);
    return `<path class="rmap-land${on ? '' : ' off'}" d="${polys.map((p) => p.map(ringPath).join('')).join('')}"/>`;
  }).join('');
  const dotsSvg = S.nodes.map((n) => { const [x, y] = P([n.lng, n.lat]); return `<circle class="rmap-dot" cx="${x}" cy="${y}" r="1.4"/>`; }).join('');
  const pinsSvg = top.map((n) => {
    const [x, y] = P([n.lng, n.lat]);
    return `<g transform="translate(${x},${y})"><circle class="pin-mark" r="8.5"/><text class="pin-text" y="3.5" text-anchor="middle">${n.rank}</text></g>`;
  }).join('');
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Map of Europe with the shortlisted regions numbered" style="font-family:'DM Sans',sans-serif"><rect class="rmap-sea" width="${W}" height="${H}"/>${paths}${dotsSvg}${pinsSvg}</svg>`;
}

function niceTicks(min, max, n = 5) {
  const raw = (max - min) / n || 1;
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  const step = (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  const out = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-6; v += step) out.push(v);
  return out;
}

function scatter(top) {
  const W = 760; const H = 360; const m = { l: 64, r: 16, t: 12, b: 44 };
  const xs = S.nodes.map((n) => n.total_cost_eur / 1e6);
  const ys = S.nodes.map((n) => n.dc_carbon_tco2_yr / 1e3);
  const xMin = Math.min(...xs); const xMax = Math.max(...xs);
  const yMin = 0; const yMax = Math.max(...ys);
  const X = (v) => (m.l + ((v - xMin) / (xMax - xMin || 1)) * (W - m.l - m.r)).toFixed(1);
  const Y = (v) => (H - m.b - ((v - yMin) / (yMax - yMin || 1)) * (H - m.t - m.b)).toFixed(1);
  const xt = niceTicks(xMin, xMax, 6).filter((v) => v >= xMin);
  const yt = niceTicks(yMin, yMax, 5);
  const grid = [
    ...xt.map((v) => `<line class="sc-grid" x1="${X(v)}" x2="${X(v)}" y1="${m.t}" y2="${H - m.b}"/><text class="sc-label" x="${X(v)}" y="${H - m.b + 16}" text-anchor="middle">${F.d1.format(v)}</text>`),
    ...yt.map((v) => `<line class="sc-grid" x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="sc-label" x="${m.l - 8}" y="${+Y(v) + 4}" text-anchor="end">${F.int.format(v)}</text>`),
  ].join('');
  const pts = S.nodes.map((n) => `<circle class="sc-dot" cx="${X(n.total_cost_eur / 1e6)}" cy="${Y(n.dc_carbon_tco2_yr / 1e3)}" r="1.8"/>`).join('');
  const tops = top.map((n) => `<g transform="translate(${X(n.total_cost_eur / 1e6)},${Y(n.dc_carbon_tco2_yr / 1e3)})"><circle class="pin-mark" r="7.5"/><text class="pin-text" y="3.3" text-anchor="middle" style="font-size:9px">${n.rank}</text></g>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Scatter of cost against carbon for every region" style="font-family:'DM Sans',sans-serif">
    ${grid}
    <line class="sc-axis" x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}"/>
    <line class="sc-axis" x1="${m.l}" x2="${m.l}" y1="${m.t}" y2="${H - m.b}"/>
    <text class="sc-title" x="${(m.l + W - m.r) / 2}" y="${H - 6}" text-anchor="middle">Cost, € M (energy per year + land term)</text>
    <text class="sc-title" transform="translate(14,${(m.t + H - m.b) / 2}) rotate(-90)" text-anchor="middle">Carbon, thousand t CO₂ per year</text>
    ${pts}${tops}
  </svg>`;
}

async function runLand() {
  const ids = S.nodes.slice(0, TOP).map((n) => n.node_id);
  let next = 0;
  landRun = 0;
  renderReport();
  const worker = async () => {
    while (next < ids.length) {
      const id = ids[next++];
      await landFetch(id);
      landRun += 1;
      if (!$('report').hidden) renderReport();
    }
  };
  await Promise.all([worker(), worker(), worker()]); // server allows 3 CNN runs at once
  landRun = null;
  if (!$('report').hidden) renderReport();
}

function showReport(on) {
  if (on) renderReport();
  $('report').hidden = !on;
  $('app').hidden = on;
  scrollTo(0, 0);
  if (!on) map.invalidateSize();
}

/* ---------------- Wiring ---------------- */

$('in-mw').addEventListener('input', () => scheduleQuery(400));
$('in-m2').addEventListener('input', () => scheduleQuery(400));
$('brief').addEventListener('submit', (e) => { e.preventDefault(); runQuery(); });
$('w-reset').addEventListener('click', () => { for (const m of METRICS) S.weights[m.key] = DEFAULT_W; S.locked.clear(); syncWeights(); scheduleQuery(0); });
$('more').addEventListener('click', () => { S.shown += PAGE; renderRows(); });

$('ledger').addEventListener('click', (e) => {
  const t = e.target.closest('button');
  if (!t) return;
  if (t.dataset.drop) { toggleCountry(t.dataset.drop); return; }
  if (t.dataset.toggle) { toggleCountry(t.dataset.toggle); return; }
  if (t.hasAttribute('data-menu')) return toggleMenu();
  if (t.hasAttribute('data-all')) { S.sel = new Set(S.universe.map((u) => u.iso)); syncCountries(); scheduleQuery(0); }
  if (t.hasAttribute('data-none')) { S.sel.clear(); syncCountries(); scheduleQuery(0); }
});
document.addEventListener('pointerdown', (e) => { if ($('ledger-menu') && !e.target.closest('#ledger')) toggleMenu(false); });

const rows = $('rows');
rows.addEventListener('click', (e) => { const id = e.target.closest('tr')?.dataset.id; if (id) select(id); });
rows.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const id = e.target.closest('tr')?.dataset.id;
  if (id) { e.preventDefault(); select(id); }
});
rows.addEventListener('mouseover', (e) => { const tr = e.target.closest('tr'); if (tr && !tr.contains(e.relatedTarget)) hot(tr.dataset.id, true); });
rows.addEventListener('mouseout', (e) => { const tr = e.target.closest('tr'); if (tr && !tr.contains(e.relatedTarget)) hot(tr.dataset.id, false); });

$('dock').addEventListener('click', (e) => {
  if (e.target.closest('[data-close]')) return closeDock();
  const land = e.target.closest('[data-land]');
  if (land) landFetch(land.dataset.land);
});
function openSources() {
  S.selected = null;
  markSelection();
  renderSources();
  loadSources();
}
$('btn-sources').addEventListener('click', () => (S.dock === 'sources' ? closeDock() : openSources()));
$('st-faults').addEventListener('click', openSources);
$('btn-export').addEventListener('click', () => showReport(true));
$('report').addEventListener('click', (e) => {
  if (e.target.closest('[data-report-close]')) showReport(false);
  else if (e.target.closest('[data-report-print]')) print();
  else if (e.target.closest('[data-report-land]') && landRun === null) runLand();
});
addEventListener('beforeprint', () => { if ($('report').hidden) showReport(true); else renderReport(); });
addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if ($('ledger-menu')) { toggleMenu(false); $('ledger').querySelector('[data-menu]')?.focus(); }
  else if (!$('report').hidden) showReport(false);
  else if (S.dock) closeDock();
});

async function init() {
  buildWeights();
  readBrief();
  renderLedger();
  // basemap, sources and the first ranking load in parallel
  const geo = fetch('countries.geojson').then((r) => r.json()).then(drawCountries).catch(() => {});
  await Promise.all([geo, loadSources(), runQuery()]);
}
init();
