document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initMobileNav();
  initMap();
  loadMapView();
  initAdminHandlers();
  initAnalyticsHandlers();
  initCSVDrop();
});

function initNav() {
  function switchView(view) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll(`[data-view="${view}"]`).forEach(t => t.classList.add('active'));
    document.getElementById('view-' + view).classList.add('active');
    if (view === 'sharks') initSharksView();
    if (view === 'analytics') loadCentrality();
  }
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => { switchView(tab.dataset.view); closeMobileNav(); });
  });
}

function initMobileNav() {
  const burger  = document.getElementById('nav-hamburger');
  const overlay = document.getElementById('mobile-nav-overlay');
  const nav     = document.getElementById('mobile-nav');
  burger.addEventListener('click', () => {
    nav.classList.toggle('hidden');
    overlay.classList.toggle('hidden');
  });
  overlay.addEventListener('click', closeMobileNav);
}

function closeMobileNav() {
  document.getElementById('mobile-nav').classList.add('hidden');
  document.getElementById('mobile-nav-overlay').classList.add('hidden');
}

function setStatus(msg) {
  const el = document.getElementById('map-status');
  if (el) el.textContent = msg;
}

async function refreshAllData() {
  try {
    State.sharks = await API.getSharks();
    State.filteredSharks = [...State.sharks];
    UI.renderSharkList(State.filteredSharks);
    refreshSpeciesSelect('filter-species', State.sharks);
    const countEl = document.getElementById('shark-count');
    if (countEl) countEl.textContent = State.sharks.length + ' tracked';

    if (typeof refreshSpeciesSelects === 'function') refreshSpeciesSelects(State.sharks);
    if (typeof refreshSharkIdSelect === 'function') refreshSharkIdSelect(State.sharks);

    const sharksView = document.getElementById('view-sharks');
    if (sharksView && sharksView.classList.contains('active')) {
      State.gridFiltered = [...State.sharks];
      refreshSpeciesSelect('table-species', State.sharks);
      renderNextGridPage(true);
    }
  } catch (e) {}

  try {
    const markers = await API.getZoneMarkers();
    State.zoneMarkers = markers;
    if (typeof renderZoneMarkers === 'function') renderZoneMarkers(markers);
    if (typeof refreshZoneIdSelect === 'function') refreshZoneIdSelect(markers);

    const sel = document.getElementById('zfp-zone');
    if (sel) {
      const currentValue = sel.value;
      const validIds = new Set(markers.map(m => m.zoneName || m.gridId).filter(Boolean));

      Array.from(sel.options).forEach(opt => {
        if (opt.value && !validIds.has(opt.value)) sel.removeChild(opt);
      });

      const existing = new Set(Array.from(sel.options).map(o => o.value));
      markers.forEach(m => {
        const zid = m.zoneName || m.gridId;
        if (zid && !existing.has(zid)) {
          const opt = document.createElement('option');
          opt.value = zid; opt.textContent = zid;
          sel.appendChild(opt);
        }
      });

      if (currentValue && validIds.has(currentValue)) {
        sel.value = currentValue;
      } else if (currentValue) {
        sel.value = '';
        if (typeof closeZonePanel === 'function') closeZonePanel();
      }
    }
  } catch (e) {}

  try {
    if (State.showClusters && typeof loadClusterMarkers === 'function') {
      await loadClusterMarkers();
    }
    const anaView = document.getElementById('view-analytics');
    if (anaView && anaView.classList.contains('active')) {
      if (typeof runAnalysis === 'function') await runAnalysis();
      if (typeof loadCentrality === 'function') await loadCentrality();
    }
  } catch (e) {}
}

function refreshSpeciesSelect(selectId, sharks) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  const currentValue = sel.value;
  UI.renderSpeciesOptions(sharks, selectId);
  const stillExists = Array.from(sel.options).some(o => o.value === currentValue);
  sel.value = stillExists ? currentValue : '';
}
