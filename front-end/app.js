const sites = [
  { name: 'Stockholm North', country: 'Sweden', lat: 59.3293, lng: 18.0686, cost: 45, carbon: 20, land: 120 },
  { name: 'Frankfurt East', country: 'Germany', lat: 50.1109, lng: 8.6821, cost: 90, carbon: 320, land: 380 },
  { name: 'Dublin Profile', country: 'Ireland', lat: 53.3498, lng: -6.2603, cost: 75, carbon: 290, land: 250 },
  { name: 'Warsaw Hub', country: 'Poland', lat: 52.2297, lng: 21.0122, cost: 80, carbon: 650, land: 90 },
  { name: 'Marseille Port', country: 'France', lat: 43.2965, lng: 5.3698, cost: 70, carbon: 50, land: 180 },
  { name: 'Madrid Solar', country: 'Spain', lat: 40.4168, lng: -3.7038, cost: 60, carbon: 120, land: 140 },
  { name: 'Amsterdam Metro', country: 'Netherlands', lat: 52.3676, lng: 4.9041, cost: 85, carbon: 270, land: 310 }
];
let map, geoJsonLayer, hoverTimeout, activeSiteName = null, activePriority = 'balanced';
let top5Countries = [], siteMarkers = [], scoredSites = [], countriesLayersMap = {};

function initMap() {
  map = L.map('europe-map', { zoomControl: true, minZoom: 3, maxZoom: 6, maxBounds: [[34, -25], [72, 40]] }).setView([52, 10], 4);
  fetch('europe.geojson').then(res => res.json()).then(data => {
    geoJsonLayer = L.geoJSON(data, {
      style: countryStyle,
      onEachFeature: (feature, layer) => {
        const name = feature.properties.NAME || feature.properties.name;
        countriesLayersMap[name] = layer;
        layer.on({
          click: () => { clearTimeout(hoverTimeout); selectCountry(name, layer, true); },
          mouseover: () => { layer.setStyle({ color: '#ffffff', weight: 2 }); clearTimeout(hoverTimeout); hoverTimeout = setTimeout(() => selectCountry(name, layer, false), 500); },
          mouseout: () => { clearTimeout(hoverTimeout); geoJsonLayer.resetStyle(layer); }
        });
      }
    }).addTo(map);
    updateDashboard();
  }).catch(err => console.error("Error loading GeoJSON:", err));
}

function countryStyle(feature) {
  const name = feature.properties.NAME || feature.properties.name;
  return { fillColor: '#f59e0b', weight: 1.2, opacity: 1, color: '#f59e0b', fillOpacity: top5Countries.includes(name) ? 0.45 : 0 };
}

function updateDashboard() {
  const capacity = parseInt(document.getElementById('param-capacity').value) || 50;
  const footprint = parseInt(document.getElementById('param-footprint').value) || 15000;
  const processed = sites.map(s => ({ ...s, price: Math.round(s.cost * (1 - (capacity - 50) * 0.0005)), co2: s.carbon, landCost: Math.round(s.land * footprint * 0.001) }));
  const minP = Math.min(...processed.map(s => s.price)), maxP = Math.max(...processed.map(s => s.price));
  const minC = Math.min(...processed.map(s => s.co2)), maxC = Math.max(...processed.map(s => s.co2));
  const minL = Math.min(...processed.map(s => s.landCost)), maxL = Math.max(...processed.map(s => s.landCost));
  scoredSites = processed.map(s => {
    const nP = 1 - (s.price - minP) / (maxP - minP || 1), nC = 1 - (s.co2 - minC) / (maxC - minC || 1), nL = 1 - (s.landCost - minL) / (maxL - minL || 1);
    const score = Math.round((activePriority === 'price' ? nP * 0.65 + nL * 0.25 + nC * 0.1 : activePriority === 'co2' ? nP * 0.1 + nL * 0.1 + nC * 0.8 : nP * 0.4 + nL * 0.2 + nC * 0.4) * 100);
    return { ...s, score };
  }).sort((a, b) => b.score - a.score);
  top5Countries = scoredSites.slice(0, 5).map(s => s.country);
  if (geoJsonLayer) geoJsonLayer.eachLayer(layer => layer.setStyle({ fillOpacity: top5Countries.includes(layer.feature.properties.NAME || layer.feature.properties.name) ? 0.45 : 0 }));
  document.getElementById('rankings-list').innerHTML = scoredSites.map((s, idx) => `
    <div class="rank-item" onclick="triggerMapSelection('${s.country}', '${s.name}')">
      <div class="rank-left"><span class="rank-badge">${idx + 1}</span><div><div class="rank-name">${s.name}</div><div class="rank-country">${s.country}</div></div></div>
      <span class="rank-score">${s.score}%</span>
    </div>`).join('');
  if (document.getElementById('panel-detail').style.display === 'block' && activeSiteName) showDetail(activeSiteName);
}

function selectCountry(countryName, layer, shouldPanZoom = true) {
  if (shouldPanZoom) map.fitBounds(layer.getBounds(), { padding: [35, 35], maxZoom: 5 });
  siteMarkers.forEach(m => map.removeLayer(m)); siteMarkers = [];
  scoredSites.filter(s => s.country === countryName).forEach((site, idx) => {
    const marker = L.circleMarker([site.lat, site.lng], { radius: 12, fillColor: '#7C5CFF', color: '#ffffff', weight: 1.5, opacity: 0.9, fillOpacity: 0.9 }).addTo(map);
    marker.bindPopup(`
      <div class="popup-title">${site.name}</div>
      <div class="popup-row"><span>Price:</span><strong>€${site.price}/MWh</strong></div>
      <div class="popup-row"><span>CO2:</span><strong>${site.co2} g</strong></div>
      <div class="popup-row"><span>Land Cost:</span><strong>€${site.landCost.toLocaleString()}</strong></div>
      <div class="popup-row"><span>Suitability:</span><strong>${site.score}%</strong></div>
      <button class="btn-prio active" onclick="showDetail('${site.name}')" style="margin-top:0.5rem; width:100%; font-size:0.75rem; padding:0.25rem; cursor:pointer; border-radius:4px; display:block; text-align:center;">View Details</button>
    `, { offset: [0, -5], autoPan: false });
    siteMarkers.push(marker);
    marker.on('click', () => showDetail(site.name));
    if (idx === 0) setTimeout(() => marker.openPopup(), 250);
  });
}

function triggerMapSelection(countryName, siteName) {
  const layer = countriesLayersMap[countryName];
  if (layer) selectCountry(countryName, layer);
  if (siteName) showDetail(siteName);
}

function showDetail(siteName) {
  activeSiteName = siteName; const site = scoredSites.find(s => s.name === siteName); if (!site) return;
  document.getElementById('detail-title').innerText = site.name; document.getElementById('detail-country').innerText = site.country;
  document.getElementById('detail-price').innerText = `€${site.price}/MWh`; document.getElementById('detail-co2').innerText = `${site.co2} g`;
  document.getElementById('detail-land').innerText = `€${(site.landCost / 1000).toFixed(0)}k`; document.getElementById('detail-score').innerText = `${site.score}%`;
  const sP = site.country === 'Spain' ? 1.5 : (site.country === 'France' ? 1.2 : 0.8), wP = site.country === 'Ireland' ? 1.5 : (site.country === 'Sweden' ? 1.3 : 0.9);
  const solar = Math.min(50, Math.round(sP * 20)), wind = Math.min(50 - solar, Math.round(wP * 25)), battery = Math.round((solar + wind) * 0.4), ppa = Math.round((100 - solar - wind) * 0.55), grid = 100 - solar - wind - ppa;
  document.getElementById('detail-mix-chart').innerHTML = `
    <div class="mix-row"><div class="mix-lbl">Solar</div><div class="mix-bar"><div class="mix-fill" style="width: ${solar}%; background: #ffd700;"></div></div><div class="mix-val">${solar}%</div></div>
    <div class="mix-row"><div class="mix-lbl">Wind</div><div class="mix-bar"><div class="mix-fill" style="width: ${wind}%; background: #00ff88;"></div></div><div class="mix-val">${wind}%</div></div>
    <div class="mix-row"><div class="mix-lbl">Battery</div><div class="mix-bar"><div class="mix-fill" style="width: ${battery}%; background: #00d2ff;"></div></div><div class="mix-val">${battery}%</div></div>
    <div class="mix-row"><div class="mix-lbl">Grid PPA</div><div class="mix-bar"><div class="mix-fill" style="width: ${ppa}%; background: #a855f7;"></div></div><div class="mix-val">${ppa}%</div></div>
    <div class="mix-row"><div class="mix-lbl">Grid Power</div><div class="mix-bar"><div class="mix-fill" style="width: ${grid}%; background: #64748b;"></div></div><div class="mix-val">${grid}%</div></div>`;
  const expl = activePriority === 'price' ? `${site.name} is selected for its low overall costs. It features a wholesale energy cost of €${site.price}/MWh and land cost of €${site.landCost.toLocaleString()}, making it a highly cost-efficient zone.` : activePriority === 'co2' ? `${site.name} is chosen for its environmental efficiency. Grid carbon intensity is extremely low at ${site.co2} gCO₂/kWh, minimizing green compliance overhead for hyperscalers.` : `${site.name} offers a balanced mix. It matches competitive pricing (€${site.price}/MWh) with solid sustainability metrics (${site.co2} gCO₂/kWh) and low local grid connection overhead.`;
  document.getElementById('detail-explanation').innerText = expl;
  document.getElementById('panel-list').style.display = 'none'; document.getElementById('panel-detail').style.display = 'block';
}
window.showDetail = showDetail; window.triggerMapSelection = triggerMapSelection;

// Submit search listener (icon with arrow)
document.getElementById('btn-submit-search').addEventListener('click', () => updateDashboard());

// Keydown listeners on input parameters (Enter submits search)
['param-capacity', 'param-footprint'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', (e) => {
    if (e.key === 'Enter') updateDashboard();
  });
});

// Skyscanner priority dropdown behavior
const dropTrigger = document.getElementById('priority-dropdown-trigger');
const dropMenu = document.getElementById('priority-dropdown-menu');
const currentPriorityText = document.getElementById('current-priority-text');
const dropdownItems = document.querySelectorAll('.sky-dropdown-item');

dropTrigger.addEventListener('click', (e) => {
  e.stopPropagation();
  const isMenuVisible = dropMenu.style.display === 'flex';
  dropMenu.style.display = isMenuVisible ? 'none' : 'flex';
  dropTrigger.classList.toggle('active', !isMenuVisible);
});

document.addEventListener('click', () => {
  dropMenu.style.display = 'none';
  dropTrigger.classList.remove('active');
});

dropdownItems.forEach(item => {
  item.addEventListener('click', (e) => {
    e.stopPropagation();
    activePriority = item.getAttribute('data-value');
    currentPriorityText.innerText = item.innerText;
    dropdownItems.forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    dropMenu.style.display = 'none';
    dropTrigger.classList.remove('active');
  });
});

document.getElementById('btn-back-list').addEventListener('click', () => { activeSiteName = null; document.getElementById('panel-detail').style.display = 'none'; document.getElementById('panel-list').style.display = 'block'; });

document.getElementById('btn-save-search').addEventListener('click', () => {
  const search = { capacity: parseInt(document.getElementById('param-capacity').value) || 50, footprint: parseInt(document.getElementById('param-footprint').value) || 15000, priority: activePriority, date: new Date().toLocaleString('en-US', { hour12: false }) };
  let saved = JSON.parse(localStorage.getItem('dc_siting_searches')) || []; saved.push(search); localStorage.setItem('dc_siting_searches', JSON.stringify(saved));
  alert('Search parameters saved successfully!');
});
document.getElementById('btn-print-site').addEventListener('click', () => window.print());

const profileCircle = document.getElementById('profile-circle'), profilePage = document.getElementById('profile-page');
const btnProfile = document.getElementById('btn-opt-profile'), btnSettings = document.getElementById('btn-opt-settings');
let hideTimeout, exploded = false;

function explodeButtons() {
  clearTimeout(hideTimeout);
  if (exploded) return;
  const buttons = [btnProfile, btnSettings];
  const N = buttons.length;
  const maxAngle = 90;
  const step = N > 1 ? maxAngle / (N - 1) : 0;
  const R = 95;
  buttons.forEach((btn, idx) => {
    const rad = ((idx * step) * Math.PI) / 180;
    btn.style.transform = `translate(${R * Math.sin(rad)}px, ${-R * Math.cos(rad)}px)`;
    btn.style.opacity = '1'; btn.style.pointerEvents = 'auto';
  });
  exploded = true;
}

function implodeImmediately() {
  clearTimeout(hideTimeout);
  [btnProfile, btnSettings].forEach(b => { b.style.transform = 'translate(0, 0)'; b.style.opacity = '0'; b.style.pointerEvents = 'none'; });
  exploded = false;
}

function implodeButtons() {
  clearTimeout(hideTimeout);
  hideTimeout = setTimeout(implodeImmediately, 1000);
}

[profileCircle, btnProfile, btnSettings].forEach(elem => {
  elem.addEventListener('mouseenter', explodeButtons);
  elem.addEventListener('mouseleave', implodeButtons);
});

document.addEventListener('click', (e) => {
  if (exploded && !profileCircle.contains(e.target) && !btnProfile.contains(e.target) && !btnSettings.contains(e.target)) {
    implodeImmediately();
  }
});

function openProfilePage(cardId) {
  profilePage.style.display = 'flex';
  profilePage.classList.remove('reveal-anim'); void profilePage.offsetWidth; profilePage.classList.add('reveal-anim');
  document.getElementById('profile-searches-card').style.display = cardId === 'searches' ? 'block' : 'none';
  document.getElementById('profile-form-card').style.display = cardId === 'profile' ? 'block' : 'none';
}

function updateProfileCircleIcon() {
  const first = localStorage.getItem('user_profile_firstname') || '';
  const btn = document.getElementById('profile-circle');
  btn.innerText = first.trim() ? first.trim().charAt(0).toUpperCase() : '👤';
  btn.style.fontWeight = first.trim() ? '700' : 'normal';
}

btnProfile.addEventListener('click', () => {
  openProfilePage('profile');
  ['firstname', 'lastname', 'email', 'company', 'role'].forEach(f => document.getElementById(`user-${f}`).value = localStorage.getItem(`user_profile_${f}`) || '');
  implodeImmediately();
});

btnSettings.addEventListener('click', () => {
  openProfilePage('searches'); renderSavedSearches();
  implodeImmediately();
});

document.querySelectorAll('.btn-back-dash').forEach(btn => {
  btn.addEventListener('click', () => { profilePage.style.display = 'none'; });
});

document.getElementById('user-profile-form').addEventListener('submit', (e) => {
  e.preventDefault();
  ['firstname', 'lastname', 'email', 'company', 'role'].forEach(f => localStorage.setItem(`user_profile_${f}`, document.getElementById(`user-${f}`).value));
  updateProfileCircleIcon();
  alert('Profile saved successfully!');
});

function renderSavedSearches() {
  const list = document.getElementById('saved-searches-list');
  const searches = JSON.parse(localStorage.getItem('dc_siting_searches')) || [];
  
  let html = `<h3>Saved Queries</h3><div class="saved-list">`;
  if (searches.length === 0) {
    html += `<div style="color: var(--text-muted); font-size: 0.85rem;">No saved queries.</div>`;
  } else {
    html += searches.map((s, idx) => `
      <div class="saved-item">
        <div class="saved-info">
          <div><strong>Query #${idx+1}:</strong> ${s.capacity} MW | ${s.footprint.toLocaleString()} m²</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">Priority: ${s.priority.toUpperCase()} | Saved: ${s.date}</div>
        </div>
        <div class="saved-actions">
          <button class="btn-prio active" onclick="loadSavedSearch(${idx})" style="font-size: 0.7rem; padding: 0.25rem 0.5rem; cursor: pointer; border-radius: 4px;">Load</button>
          <button class="btn-prio" onclick="deleteSavedSearch(${idx})" style="font-size: 0.7rem; padding: 0.25rem 0.5rem; cursor: pointer; border-radius: 4px; border-color: var(--border);">Delete</button>
        </div>
      </div>`).join('');
  }
  html += `</div>`;
  list.innerHTML = html;
}

window.loadSavedSearch = (idx) => {
  const saved = JSON.parse(localStorage.getItem('dc_siting_searches')) || [], s = saved[idx];
  if (s) {
    document.getElementById('param-capacity').value = s.capacity; document.getElementById('param-footprint').value = s.footprint; activePriority = s.priority;
    const activeItem = Array.from(dropdownItems).find(item => item.getAttribute('data-value') === s.priority);
    if (activeItem) {
      currentPriorityText.innerText = activeItem.innerText;
      dropdownItems.forEach(i => i.classList.remove('active'));
      activeItem.classList.add('active');
    }
    updateDashboard(); profilePage.style.display = 'none';
  }
};
window.deleteSavedSearch = (idx) => {
  let saved = JSON.parse(localStorage.getItem('dc_siting_searches')) || []; saved.splice(idx, 1); localStorage.setItem('dc_siting_searches', JSON.stringify(saved));
  renderSavedSearches();
};

window.addEventListener('DOMContentLoaded', () => { initMap(); updateProfileCircleIcon(); });
