/**
 * app.js — SharkTrack application logic
 */

const State = {
  sharks: [],
  filteredSharks: [],
  selectedShark: null,
  selectedSharkTrajectory: null,   // full trajectory cache {sharkId, trajectory:[]}
  map: null,
  zoneMarkers: [],
  trajectoryLayer: null,
  zoneTrajectoryLayers: [],
  showZones: true,
  showClusters: false,
  adminAuthed: false,
  // pagination for sharks grid
  gridPage: 0,
  gridPageSize: 30,
  gridFiltered: [],
};

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initMobileNav();
  initMap();
  loadMapView();
  initAdminHandlers();
  initAnalyticsHandlers();
  initCSVDrop();
});

// ═══════════════════════════════════════════
// NAV
// ═══════════════════════════════════════════
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
    tab.addEventListener('click', () => {
      switchView(tab.dataset.view);
      closeMobileNav();
    });
  });
}

function initMobileNav() {
  const burger = document.getElementById('nav-hamburger');
  const overlay = document.getElementById('mobile-nav-overlay');
  const nav = document.getElementById('mobile-nav');

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

// ═══════════════════════════════════════════
// MAP
// ═══════════════════════════════════════════
function initMap() {
  State.map = L.map('map', { center: [20, -30], zoom: 3 });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap', maxZoom: 18,
  }).addTo(State.map);

  // 1. Obsługa przycisku ZONES (Włącza/wyłącza warstwę I otwiera panel dat)
  document.getElementById('ctrl-zones').addEventListener('click', function () {
    State.showZones = !State.showZones;
    this.classList.toggle('active', State.showZones);

    const panel = document.getElementById('zone-filter-panel');
    if (State.showZones) {
      panel.classList.remove('hidden'); // Show panel when turning layer ON
    } else {
      panel.classList.add('hidden');    // Hide panel when turning layer OFF
      closeZonePanel();
      State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
      State.zoneTrajectoryLayers = [];
    }
    refreshMapLayers();
  });

  // 2. Obsługa przycisku CLUSTERS (Włącza/wyłącza warstwę I otwiera panel dat)
  document.getElementById('ctrl-clusters').addEventListener('click', function () {
    State.showClusters = !State.showClusters;
    this.classList.toggle('active', State.showClusters);

    const clusterPanel = document.getElementById('cluster-filter-panel');
    if (State.showClusters) {
      clusterPanel.classList.remove('hidden'); // Show panel when turning layer ON
      loadClusterMarkers();
    } else {
      clusterPanel.classList.add('hidden');    // Hide panel when turning layer OFF
      refreshMapLayers();
    }
  });

  // 3. Zamknięcie panelu wyboru stref za pomocą krzyżyka ✕ (ZFP)
  document.getElementById('zfp-close').addEventListener('click', () => {
    // Hide ONLY the HTML box element
    document.getElementById('zone-filter-panel').classList.add('hidden');
    // State.showZones and button active class are NOT changed, so data stays on map
  });

  // 4. Zamknięcie panelu klastrów za pomocą krzyżyka ✕ (CFP)
  document.getElementById('cfp-close')?.addEventListener('click', () => {
    // Hide ONLY the HTML box element
    document.getElementById('cluster-filter-panel').classList.add('hidden');
    // State.showClusters and button active class are NOT changed, so data stays on map
  });

  // Reakcja na zmianę wybranej strefy w liście rozwijanej
  document.getElementById('zfp-zone').addEventListener('change', function() {
    if (this.value) {
      openZonePanel(this.value);
    } else {
      closeZonePanel();
    }
    refreshMapLayers();
  });

  // 5. Reakcja na zmianę dat w panelu ZONE FOCUS
  document.getElementById('zfp-start')?.addEventListener('input', triggerZoneRefresh);
  document.getElementById('zfp-end')?.addEventListener('input', triggerZoneRefresh);

  // 6. Reakcja na zmianę dat w panelu CLUSTER FOCUS i synchronizacja w locie z Analytics
  document.getElementById('cfp-start')?.addEventListener('input', () => {
    const val = document.getElementById('cfp-start').value;
    const anaStartEl = document.getElementById('ana-start');
    if (anaStartEl) anaStartEl.value = val;
    loadClusterMarkers();
  });

  document.getElementById('cfp-end')?.addEventListener('input', () => {
    const val = document.getElementById('cfp-end').value;
    const anaEndEl = document.getElementById('ana-end');
    if (anaEndEl) anaEndEl.value = val;
    loadClusterMarkers();
  });

  document.getElementById('drawer-close').addEventListener('click', closeDrawer);
  document.getElementById('zone-panel-close').addEventListener('click', closeZonePanel);
}

async function loadMapView() {
  await Promise.all([loadSharks(), loadZoneMarkers()]);
  populateZoneFilterDropdown();
}

async function loadSharks() {
  try {
    State.sharks = await API.getSharks();
    State.filteredSharks = [...State.sharks];
    UI.renderSharkList(State.filteredSharks);
    UI.renderSpeciesOptions(State.sharks, 'filter-species');
    document.getElementById('shark-count').textContent = State.sharks.length + ' tracked';
    setStatus('Loaded ' + State.sharks.length + ' sharks');
    initSidebarFilters();
  } catch (e) {
    setStatus('Error: ' + e.message);
    document.getElementById('shark-list').innerHTML = '<div class="loading-msg">Failed to load sharks.</div>';
  }
}

async function loadZoneMarkers() {
  try {
    const markers = await API.getZoneMarkers();
    State.zoneMarkers = markers;

    const globalBounds = await API.getZoneBounds("ALL_ZONES");

    State.globalTimeBounds = {
      start: globalBounds.start.replace(' ', 'T').substring(0, 16),
      end: globalBounds.end.replace(' ', 'T').substring(0, 16)
    };

    // 1. Kontrola dat dla suwaków na MAPIE (Panel ZONE FOCUS)
    const startEl = document.getElementById('zfp-start');
    const endEl = document.getElementById('zfp-end');
    if (startEl && endEl) {
      startEl.min = State.globalTimeBounds.start; startEl.max = State.globalTimeBounds.end;
      endEl.min = State.globalTimeBounds.start;   endEl.max = State.globalTimeBounds.end;
      startEl.value = State.globalTimeBounds.start;
      endEl.value = State.globalTimeBounds.end;
    }

    // 2. Kontrola dat dla panelu ANALYTICS
    const anaStartEl = document.getElementById('ana-start');
    const anaEndEl   = document.getElementById('ana-end');
    if (anaStartEl && anaEndEl) {
      anaStartEl.min = State.globalTimeBounds.start; anaStartEl.max = State.globalTimeBounds.end;
      anaEndEl.min   = State.globalTimeBounds.start; anaEndEl.max   = State.globalTimeBounds.end;
      anaStartEl.value = State.globalTimeBounds.start;
      anaEndEl.value   = State.globalTimeBounds.end;
    }

    // 3. Kontrola dat dla suwaków nowego panelu na MAPIE (Panel CLUSTER FOCUS)
    const cfpStartEl = document.getElementById('cfp-start');
    const cfpEndEl   = document.getElementById('cfp-end');
    if (cfpStartEl && cfpEndEl) {
      cfpStartEl.min = State.globalTimeBounds.start; cfpStartEl.max = State.globalTimeBounds.end;
      cfpEndEl.min   = State.globalTimeBounds.start; cfpEndEl.max   = State.globalTimeBounds.end;
      cfpStartEl.value = State.globalTimeBounds.start;
      cfpEndEl.value   = State.globalTimeBounds.end;
    }

    if (State.showZones) renderZoneMarkers(markers);
  } catch (e) {
    setStatus('Zone data unavailable');
  }
}


function renderZoneMarkers(markers) {
  if (_zoneLayerGroup) State.map.removeLayer(_zoneLayerGroup);
  _zoneLayerGroup = L.layerGroup();
  markers.forEach(m => {
    if (!m.lat || !m.lon) return;
    const icon = L.divIcon({
      className: '',
      html: `<div class="zone-marker-icon" style="width:26px;height:26px;">${m.uniqueSharksCount || 0}</div>`,
      iconSize: [26, 26], iconAnchor: [13, 13],
    });

    // Pobieramy identyfikator strefy
    const currentGridId = m.gridId || m.zoneName;

    L.marker([m.lat, m.lon], { icon, gridId: currentGridId })
      .bindPopup(`<strong>${currentGridId || 'Zone'}</strong><br>Sharks: ${m.uniqueSharksCount || 0}`)
      .on('click', () => {
        // KROK 1: Jeśli klikamy marker na mapie, ustawiamy select na tę strefę
        const sel = document.getElementById('zfp-zone');
        if (sel) sel.value = currentGridId;

        // KROK 2: Otwieramy panel boczny strefy
        openZonePanel(currentGridId);

        // KROK 3: Odświeżamy warstwy, by schować pozostałe strefy
        refreshMapLayers();
      })
      .addTo(_zoneLayerGroup);
  });
  if (State.showZones) _zoneLayerGroup.addTo(State.map);
}

// ═══════════════════════════════════════════
// MAP LAYERS
// ═══════════════════════════════════════════
let _zoneLayerGroup = null;
let _clusterLayerGroup = null;

function refreshMapLayers() {
  if (_zoneLayerGroup) {
    if (State.showZones) {
      const selectedZoneId = document.getElementById('zfp-zone')?.value;

      _zoneLayerGroup.eachLayer(layer => {
        // Pobieramy ID strefy przypisane do markera (sprawdzamy oba klucze dla bezpieczeństwa)
        const markerGridId = layer.options.gridId || layer.options.zoneName;

        if (!selectedZoneId || markerGridId === selectedZoneId) {
          // Jeśli marker powinien być widoczny, a nie ma go na mapie — dodajemy go płynnie
          if (!State.map.hasLayer(layer)) {
            layer.addTo(State.map);
          }
        } else {
          // Usuwamy z mapy TYLKO te markery, które nie pasują do filtra, nie ruszając reszty strefy
          if (State.map.hasLayer(layer)) {
            State.map.removeLayer(layer);
          }
        }
      });

      // Upewniamy się, że główna grupa jest na mapie
      if (!State.map.hasLayer(_zoneLayerGroup)) {
        _zoneLayerGroup.addTo(State.map);
      }
    } else {
      // Jeśli użytkownik wyłączył strefy przyciskiem, usuwamy je z mapy
      _zoneLayerGroup.eachLayer(layer => {
        if (State.map.hasLayer(layer)) State.map.removeLayer(layer);
      });
      State.map.removeLayer(_zoneLayerGroup);
    }
  }

  if (_clusterLayerGroup) {
    if (State.showClusters) {
      if (!State.map.hasLayer(_clusterLayerGroup)) _clusterLayerGroup.addTo(State.map);
    } else {
      if (State.map.hasLayer(_clusterLayerGroup)) State.map.removeLayer(_clusterLayerGroup);
    }
  }
}

async function loadClusterMarkers() {
  try {
    // ZMIANA: Odczytujemy daty z nowego panelu CLUSTER FOCUS (cfp-start, cfp-end)
    const startInput = document.getElementById('cfp-start')?.value;
    const endInput   = document.getElementById('cfp-end')?.value;

    const start = (startInput || '2000-01-01T00:00').replace('T', ' ') + ':00';
    const end   = (endInput   || '2030-12-31T23:59').replace('T', ' ') + ':00';

    const data = await API.getClusters(start, end, 20);
    if (_clusterLayerGroup) State.map.removeLayer(_clusterLayerGroup);
    _clusterLayerGroup = L.layerGroup();

    if (!data.clusters || !data.clusters.length) return;

    const maxPings = Math.max(...data.clusters.map(c => c.totalPings), 1);
    data.clusters.forEach(c => {
      const ratio = c.totalPings / maxPings;
      L.circleMarker([c.centerLat, c.centerLon], {
        radius: Math.round(14 + ratio * 22),
        fillColor: '#00e5c8',
        color: '#00e5c8',
        weight: 1,
        opacity: 0.3 + ratio * 0.5,
        fillOpacity: (0.3 + ratio * 0.5) * 0.35,
      }).bindPopup(`<strong>${c.gridId}</strong><br>Pings: ${c.totalPings}<br>Sharks: ${c.uniqueSharksCount}`)
        .addTo(_clusterLayerGroup);
    });
    if (State.showClusters) _clusterLayerGroup.addTo(State.map);
  } catch (e) {
    setStatus('Cluster data unavailable');
  }
}

// ═══════════════════════════════════════════
// ZONE FILTER → trajectories of all sharks in zone
// ═══════════════════════════════════════════
function populateZoneFilterDropdown() {
  const sel = document.getElementById('zfp-zone');
  State.zoneMarkers.forEach(m => {
    if (!m.zoneName) return;
    const opt = document.createElement('option');
    opt.value = m.zoneName;
    opt.textContent = m.zoneName;
    sel.appendChild(opt);
  });
}

async function runZoneTrajectoryFilter() {
  const gridId = document.getElementById('zfp-zone').value;
  const msg   = document.getElementById('zfp-msg');

  if (!gridId) {
    if (msg) { msg.className = 'form-msg error'; msg.textContent = 'Select a zone first.'; }
    return;
  }
  if (msg) { msg.className = 'form-msg'; msg.textContent = 'Loading zone trajectories…'; }

  // Czyszczenie starych linii trajektorii z mapy
  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];

  // Pobieramy aktualne filtry dat z kalendarzy na mapie
  const startEl = document.getElementById('zfp-start');
  const endEl = document.getElementById('zfp-end');
  const startParam = startEl?.value ? startEl.value.replace('T', ' ') + ':00' : null;
  const endParam   = endEl?.value ? endEl.value.replace('T', ' ') + ':00' : null;

  try {
    // JEDNO, lekkie zapytanie do bazy o trajektorie ograniczone do strefy i czasu
    const sharksTrajectories = await API.getZoneTrajectories(gridId, startParam, endParam);

    if (!sharksTrajectories.length) {
      if (msg) { msg.className = 'form-msg error'; msg.textContent = 'No movements in this zone for selected period.'; }
      return;
    }

    const COLORS = ['#00e5c8','#0099ff','#ff6b35','#a855f7','#f59e0b','#ec4899','#22c55e','#ef4444'];
    const bounds = [];

    // Przetwarzamy dane zwrócone z jednego zapytania backendu
    sharksTrajectories.forEach((sharkData, i) => {
      const traj = sharkData.trajectory || [];
      const pts = traj.map(p => [p.lat, p.lon]);
      if (!pts.length) return;

      const color = COLORS[i % COLORS.length];
      const line = L.polyline(pts, { color, weight: 2, opacity: 0.75, dashArray: '5 4' });
      const dotLayer = L.layerGroup();

      pts.forEach((pt, j) => {
        const isFirst = (j === 0);
        const isLast  = (j === pts.length - 1);

        L.circleMarker(pt, {
          radius: (isFirst || isLast) ? 12 : 6,
          fillColor: isFirst ? '#0099ff' : (isLast ? '#22c55e' : color),
          color: '#060d18',
          weight: 1.5,
          fillOpacity: 1,
        }).bindTooltip(`${sharkData.name || sharkData.sharkId} — ${traj[j]?.timestamp || ''}`, { direction: 'top' })
          .addTo(dotLayer);
      });

      const layer = L.layerGroup([line, dotLayer]).addTo(State.map);
      State.zoneTrajectoryLayers.push(layer);
      pts.forEach(pt => bounds.push(pt));
    });

    if (bounds.length) State.map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });

    const trajBtn = document.getElementById('zone-traj-all-btn');
    if (typeof setZoneTrajBtnToHide === 'function') {
      setZoneTrajBtnToHide(trajBtn);
    }

    if (msg) {
      msg.className = 'form-msg success';
      msg.textContent = `✓ Showing trajectories for ${sharksTrajectories.length} sharks inside ${gridId}`;
    }
  } catch (e) {
    if (msg) {
      msg.className = 'form-msg error';
      msg.textContent = '✗ ' + e.message;
    }
  }
}
// ═══════════════════════════════════════════
// SHARK SELECT / DRAWER
// ═══════════════════════════════════════════
// function selectShark(shark) {
//   State.selectedShark = shark;
//   State.selectedSharkTrajectory = null;
//   document.querySelectorAll('.shark-card').forEach(c => c.classList.remove('active'));
//   const card = document.querySelector(`.shark-card[data-id="${shark.sharkId}"]`);
//   if (card) card.classList.add('active');
//   openDrawer(shark);
// }

function openDrawer(shark) {
  // First render without trajectory bounds (we don't have them yet)
  document.getElementById('drawer-content').innerHTML = UI.buildDrawerHTML(shark, null);
  document.getElementById('shark-drawer').classList.add('open');
  wireDrawerButtons(shark);
}

function wireDrawerButtons(shark) {
  // Pre-fetch trajectory to get date bounds
  fetchTrajectoryMeta(shark.sharkId);

  document.getElementById('trajectory-btn')?.addEventListener('click', () => {
    applyTrajectoryFilter(shark.sharkId);
  });

  document.querySelectorAll('.js-gt-picker').forEach(input => {
    input.addEventListener('click', () => {
      if (typeof input.showPicker === 'function') {
        input.showPicker();
      }
    });
  });
}

async function fetchTrajectoryMeta(sharkId) {
  try {
    const data = await API.getTrajectory(sharkId);
    State.selectedSharkTrajectory = data;
    // Update the date pickers with real bounds
    if (data.trajectory && data.trajectory.length) {
      const ts = data.trajectory.map(p => p.timestamp).filter(Boolean).sort();
      const first = ts[0];
      const last  = ts[ts.length - 1];
      const startEl = document.getElementById('traj-start');
      const endEl   = document.getElementById('traj-end');
      if (startEl && endEl && first && last) {
        // timestamps like "2021-03-15 14:22:00" → need "2021-03-15T14:22"
        startEl.min = toDatetimeLocal(first);
        startEl.max = toDatetimeLocal(last);
        endEl.min   = toDatetimeLocal(first);
        endEl.max   = toDatetimeLocal(last);
        startEl.value = toDatetimeLocal(first);
        endEl.value   = toDatetimeLocal(last);
      }
    }
  } catch (_) {}
}

function toDatetimeLocal(ts) {
  // "2021-03-15 14:22:00" → "2021-03-15T14:22"
  if (!ts) return '';
  return ts.replace(' ', 'T').substring(0, 16);
}

async function applyTrajectoryFilter(sharkId) {
  const btn = document.getElementById('trajectory-btn');


  if (State.trajectoryLayer && btn && btn.textContent.includes('HIDE')) {
    State.map.removeLayer(State.trajectoryLayer);
    State.trajectoryLayer = null;
    document.getElementById('trajectory-bar').innerHTML = '';
    btn.textContent = '◉ SHOW TRAJECTORY';
    btn.classList.remove('btn-active-hide');
    return;
  }

  if (btn) { btn.textContent = 'LOADING…'; btn.disabled = true; }

  const startVal = document.getElementById('traj-start')?.value;
  const endVal   = document.getElementById('traj-end')?.value;

  try {
    let data = State.selectedSharkTrajectory;
    if (!data) data = await API.getTrajectory(sharkId);

    let traj = data.trajectory || [];

    if (startVal && endVal) {
      const s = startVal.replace('T', ' ') + ':00';
      const e = endVal.replace('T', ' ')   + ':00';
      traj = traj.filter(p => {
        if (!p.timestamp) return true;
        return p.timestamp >= s && p.timestamp <= e;
      });
    }

    if (!traj.length) throw new Error('No points in selected range');

    if (State.trajectoryLayer) State.map.removeLayer(State.trajectoryLayer);

    const pts = traj.map(p => [p.lat, p.lon]);
    const line = L.polyline(pts, { color: '#00e5c8', weight: 2, opacity: 0.85, dashArray: '4 4' });
    const dotLayer = L.layerGroup();
    const sharkName = State.selectedShark?.name || 'Shark'; // Pobranie imienia z aktualnego stanu

    pts.forEach((pt, i) => {
      L.circleMarker(pt, {
        radius: (i === 0 || i === pts.length - 1) ? 12 : 6,
       fillColor: i === 0 ? '#0099ff' : (i === pts.length - 1 ? '#22c55e' : '#00e5c8'),
        color: '#060d18', weight: 1.5, fillOpacity: 1,
      }).bindTooltip(`${sharkName} — ${traj[i]?.timestamp || ''}`, { direction: 'top' }).addTo(dotLayer);
    });

    State.trajectoryLayer = L.layerGroup([line, dotLayer]).addTo(State.map);
    State.map.fitBounds(line.getBounds(), { padding: [40, 40] });
    UI.renderTrajectoryTimeline(traj);

    if (btn) {
      btn.textContent = '✕ HIDE TRAJECTORY';
      btn.disabled = false;
      btn.classList.add('btn-active-hide');
    }
  } catch (e) {
    if (btn) { btn.textContent = 'NO DATA'; btn.disabled = false; }
  }
}

function closeDrawer() {
  document.getElementById('shark-drawer').classList.remove('open');
  if (State.trajectoryLayer) { State.map.removeLayer(State.trajectoryLayer); State.trajectoryLayer = null; }
  document.querySelectorAll('.shark-card').forEach(c => c.classList.remove('active'));
  State.selectedShark = null;
  State.selectedSharkTrajectory = null;
}

// ═══════════════════════════════════════════
// ZONE PANEL
// ═══════════════════════════════════════════
// ===========================================================================
// ZONE PANEL MANAGEMENT
// ===========================================================================

async function openZonePanel(gridId) {
  if (!gridId) return;

  // 1. Automatyczne czyszczenie linii trajektorii z mapy przy zmianie strefy
  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];

  const panel = document.getElementById('zone-panel');
  document.getElementById('zone-panel-content').innerHTML = '<div class="loading-msg">Loading zone…</div>';
  panel.classList.add('open');

  const startEl = document.getElementById('zfp-start');
  const endEl = document.getElementById('zfp-end');

  // Sprawdzamy czy użytkownik przełączył strefę na inną
  const isNewZone = startEl && startEl.getAttribute('data-current-zone') !== gridId;

  try {
    // 2. Jeśli strefa jest nowa, najpierw pytamy dedykowany endpoint o jej unikalne granice pingu
    if (isNewZone && startEl && endEl) {
      const bounds = await API.getZoneBounds(gridId);

      const apiMin = bounds.start.replace(' ', 'T').substring(0, 16);
      const apiMax = bounds.end.replace(' ', 'T').substring(0, 16);

      // Nakładamy sztywne i nieprzekraczalne ograniczenia na kalendarz HTML
      startEl.min = apiMin; startEl.max = apiMax;
      endEl.min = apiMin;   endEl.max = apiMax;

      // Ustawiamy suwaki domyślnie na skrajne wykryte daty tej strefy
      startEl.value = apiMin;
      endEl.value = apiMax;

      startEl.setAttribute('data-current-zone', gridId);
    }

    // 3. Pobieramy aktualne (lub nowo nałożone) wartości filtrów czasowych
    const startParam = startEl?.value ? startEl.value.replace('T', ' ') + ':00' : null;
    const endParam   = endEl?.value ? endEl.value.replace('T', ' ') + ':00' : null;

    // Pobieramy przefiltrowaną listę rekinów z API
    const data = await API.getZone(gridId, startParam, endParam);
    document.getElementById('zone-panel-content').innerHTML = UI.buildZonePanelHTML(data);

    // Obsługa przycisku linii trajektorii
    const trajBtn = document.getElementById('zone-traj-all-btn');
    trajBtn?.addEventListener('click', () => {
      if (State.zoneTrajectoryLayers.length > 0) {
        State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
        State.zoneTrajectoryLayers = [];
        trajBtn.textContent = '◉ SHOW ALL TRAJECTORIES IN THIS ZONE';
        trajBtn.style.background = 'rgba(0, 229, 200, 0.08)';
        trajBtn.style.color = 'var(--accent)';
        trajBtn.style.borderColor = 'rgba(0, 229, 200, 0.3)';
      } else {
        runZoneTrajectoryFilter();
      }
    });
  } catch (e) {
    document.getElementById('zone-panel-content').innerHTML = `<div class="loading-msg">Zone processing failed.</div>`;
  }
}

function closeZonePanel() {
  const panel = document.getElementById('zone-panel');
  if (panel) panel.classList.remove('open');

  const sel = document.getElementById('zfp-zone');
  if (sel) sel.value = "";

  const startEl = document.getElementById('zfp-start');
  const endEl = document.getElementById('zfp-end');

  if (startEl && endEl) {
    startEl.removeAttribute('data-current-zone');

    const gMin = State.globalTimeBounds?.start || "2018-01-01T00:00";
    const gMax = State.globalTimeBounds?.end   || "2026-12-31T23:59";

    // Przywrócenie pełnego globalnego zakresu
    startEl.min = gMin; startEl.max = gMax;
    endEl.min = gMin;   endEl.max = gMax;
    startEl.value = gMin;
    endEl.value = gMax;
  }

  // Czyszczenie trajektorii z mapy
  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];

  refreshMapLayers();
}
function triggerZoneRefresh() {
  const currentZone = document.getElementById('zfp-zone')?.value;
  const zonePanel = document.getElementById('zone-panel');
  if (currentZone && zonePanel && zonePanel.classList.contains('open')) {
    openZonePanel(currentZone);
  }
}

function setZoneTrajBtnToHide(btn) {
  if (!btn) return;
  btn.textContent = '✕ HIDE ALL TRAJECTORIES';
  btn.style.background = 'rgba(255, 62, 94, 0.08)';
  btn.style.color = 'var(--danger)';
  btn.style.borderColor = 'rgba(255, 62, 94, 0.3)';
}

// ═══════════════════════════════════════════
// SIDEBAR FILTERS
// ═══════════════════════════════════════════
function initSidebarFilters() {
  const search  = document.getElementById('filter-search');
  const species = document.getElementById('filter-species');
  function filter() {
    const q = search.value.toLowerCase();
    const s = species.value.toLowerCase();
    State.filteredSharks = State.sharks.filter(sh => {
      const mQ = !q || sh.name.toLowerCase().includes(q) || (sh.sharkId || '').toLowerCase().includes(q);
      const mS = !s || (sh.species || '').toLowerCase().includes(s);
      return mQ && mS;
    });
    UI.renderSharkList(State.filteredSharks);
  }
  search.addEventListener('input', filter);
  species.addEventListener('change', filter);
}

// ═══════════════════════════════════════════
// SHARKS VIEW — pagination / infinite scroll
// ═══════════════════════════════════════════
async function initSharksView() {
  const area = document.getElementById('sharks-scroll-area');
  area.scrollTop = 0;
  State.gridPage = 0;
  const grid = document.getElementById('shark-grid');
  grid.innerHTML = '<div class="loading-msg">Loading…</div>';

  try {
    let sharks = State.sharks.length ? State.sharks : await API.getSharks();
    if (!State.sharks.length) State.sharks = sharks;

    State.gridFiltered = [...sharks];
    UI.renderSpeciesOptions(sharks, 'table-species');
    setupTableFilters();
    setupGridClick(); // Initialize click handler once
    renderNextGridPage(true);
    initGridInfiniteScroll();
  } catch (e) {
    grid.innerHTML = '<div class="loading-msg">Failed to load.</div>';
  }
}

function renderNextGridPage(reset = false) {
  const grid = document.getElementById('shark-grid');
  if (reset) { grid.innerHTML = ''; State.gridPage = 0; }

  const start = State.gridPage * State.gridPageSize;
  const slice = State.gridFiltered.slice(start, start + State.gridPageSize);
  if (!slice.length && reset) {
    grid.innerHTML = '<div class="loading-msg">No sharks found.</div>';
    return;
  }
  slice.forEach(s => {
    const el = UI.buildGridCard(s);
    // Ensure the card element has a data attribute for event delegation
    el.setAttribute('data-shark-id', s.sharkId || s.id);
    grid.appendChild(el);
  });
  State.gridPage++;
}

function initGridInfiniteScroll() {
  const sentinel = document.getElementById('load-sentinel');
  if (!sentinel) return;

  // Disconnect previous observer if it exists to avoid duplicates
  if (window.sharkGridObserver) {
    window.sharkGridObserver.disconnect();
  }

  window.sharkGridObserver = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      const total = State.gridFiltered.length;
      if (State.gridPage * State.gridPageSize < total) renderNextGridPage();
    }
  }, { rootMargin: '200px' });

  window.sharkGridObserver.observe(sentinel);
}

function setupTableFilters() {
  const search  = document.getElementById('table-search');
  const species = document.getElementById('table-species');

  function filter() {
    // Read directly from the current DOM elements
    const q = document.getElementById('table-search').value.toLowerCase();
    const s = document.getElementById('table-species').value.toLowerCase();

    State.gridFiltered = State.sharks.filter(sh => {
      const mQ = !q || sh.name.toLowerCase().includes(q) || (sh.sharkId || '').toLowerCase().includes(q);
      const mS = !s || (sh.species || '').toLowerCase().includes(s);
      return mQ && mS;
    });
    renderNextGridPage(true);
  }

  // Remove old listeners by replacing elements with clones
  const ns = search.cloneNode(true); search.parentNode.replaceChild(ns, search);
  const nsp = species.cloneNode(true); species.parentNode.replaceChild(nsp, species);

  ns.addEventListener('input', filter);
  nsp.addEventListener('change', filter);
}

// Event delegation for handling clicks on dynamically rendered shark cards
function setupGridClick() {
  const grid = document.getElementById('shark-grid');

  // Remove existing listener before adding a new one
  grid.removeEventListener('click', handleGridClick);
  grid.addEventListener('click', handleGridClick);
}

function handleGridClick(e) {
  // Find the closest card element that contains the shark ID
  const card = e.target.closest('[data-shark-id]');
  if (!card) return;

  const sharkId = card.getAttribute('data-shark-id');

  // Znajdź pełny obiekt rekina w stanie aplikacji na podstawie sharkId
  const shark = State.sharks.find(s => s.sharkId === sharkId || s.id === sharkId);
  if (shark) {
    // Wywołanie istniejącej funkcji przenoszącej na mapę i otwierającej drawer
    selectSharkFromGrid(shark);
  }
  // Call your existing click/view details function here, e.g.:
  // Actions.viewSharkDetails(sharkId);
}
// ═══════════════════════════════════════════
// ANALYTICS
// ═══════════════════════════════════════════
function initAnalyticsHandlers() {
  document.getElementById('ana-run').addEventListener('click', runAnalysis);
}

async function runAnalysis() {
  const startInput = document.getElementById('ana-start').value;
  const endInput   = document.getElementById('ana-end').value;

  // Konwersja formatu 'YYYY-MM-DDTHH:MM' -> 'YYYY-MM-DD HH:MM:SS'
  const start = (startInput || '2000-01-01T00:00').replace('T', ' ') + ':00';
  const end   = (endInput   || '2030-12-31T23:59').replace('T', ' ') + ':00';

  const limit = parseInt(document.getElementById('ana-limit').value) || 10;
  const grid  = document.getElementById('analytics-grid');
  grid.innerHTML = '<div class="loading-msg">Running analysis…</div>';

  try {
    const data = await API.getClusters(start, end, limit);
    UI.renderClusters(data.clusters);
  } catch (e) {
    grid.innerHTML = '<div class="loading-msg">Failed: ' + e.message + '</div>';
  }
}

async function loadCentrality() {
  const grid = document.getElementById('centrality-grid');
  grid.innerHTML = '<div class="loading-msg">Loading…</div>';
  try {
    const data = await API.getDegreeCentrality(10);
    UI.renderCentrality(data.results);
  } catch (e) {
    grid.innerHTML = '<div class="loading-msg">Failed: ' + e.message + '</div>';
  }
}

// ═══════════════════════════════════════════
// ADMIN
// ═══════════════════════════════════════════
function initAdminHandlers() {
  document.getElementById('auth-login').addEventListener('click', async () => {
    const user = document.getElementById('auth-user').value.trim();
    const pass = document.getElementById('auth-pass').value;
    const err  = document.getElementById('auth-error');
    err.textContent = '';
    try {
      if (await API.verifyAdmin(user, pass)) {
        API.setCredentials(user, pass);
        document.getElementById('admin-auth-wall').classList.add('hidden');
        document.getElementById('admin-panel').classList.remove('hidden');
      } else { err.textContent = 'Invalid credentials.'; }
    } catch (e) { err.textContent = 'Auth error: ' + e.message; }
  });

  document.querySelectorAll('.admin-subtab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.admin-subtab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.admin-subpanel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.panel).classList.add('active');
    });
  });

  // Create shark
  document.getElementById('sc-submit').addEventListener('click', async () => {
    const msg = document.getElementById('sc-msg');
    try {
      const d = {
        sharkId: document.getElementById('sc-id').value.trim(),
        name:    document.getElementById('sc-name').value.trim(),
        species: document.getElementById('sc-species').value.trim(),
        gender:  document.getElementById('sc-gender').value,
        length:  parseFloat(document.getElementById('sc-length').value),
        weight:  parseFloat(document.getElementById('sc-weight').value),
      };
      if (!d.sharkId || !d.name || !d.species) throw new Error('Fill required fields.');
      await API.createShark(d);
      msg.className = 'form-msg success'; msg.textContent = '✓ Shark created.';
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  // Load for edit
  document.getElementById('se-load').addEventListener('click', async () => {
    const id = document.getElementById('se-id').value.trim();
    if (!id) return;
    try {
      const s = await API.searchShark(id);
      document.getElementById('se-name').value   = s.name    || '';
      document.getElementById('se-species').value= s.species || '';
      document.getElementById('se-gender').value = s.gender  || 'Unknown';
      document.getElementById('se-length').value = s.length  || '';
      document.getElementById('se-weight').value = s.weight  || '';
      document.getElementById('shark-edit-form').classList.remove('hidden');
    } catch (e) {
      document.getElementById('se-msg').className = 'form-msg error';
      document.getElementById('se-msg').textContent = '✗ ' + e.message;
    }
  });

  document.getElementById('se-save').addEventListener('click', async () => {
    const id = document.getElementById('se-id').value.trim();
    const msg = document.getElementById('se-msg');
    try {
      await API.updateShark(id, {
        name:    document.getElementById('se-name').value.trim(),
        species: document.getElementById('se-species').value.trim(),
        gender:  document.getElementById('se-gender').value,
        length:  parseFloat(document.getElementById('se-length').value),
        weight:  parseFloat(document.getElementById('se-weight').value),
      });
      msg.className = 'form-msg success'; msg.textContent = '✓ Updated.';
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('se-delete').addEventListener('click', async () => {
    const id = document.getElementById('se-id').value.trim();
    const msg = document.getElementById('se-msg');
    if (!confirm(`Delete shark "${id}"?`)) return;
    try {
      await API.deleteShark(id);
      msg.className = 'form-msg success'; msg.textContent = '✓ Deleted.';
      document.getElementById('shark-edit-form').classList.add('hidden');
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  // Zones
  document.getElementById('zc-submit').addEventListener('click', async () => {
    const msg = document.getElementById('zc-msg');
    try {
      const d = {
        gridId:    document.getElementById('zc-id').value.trim(),
        centerLat: parseFloat(document.getElementById('zc-lat').value),
        centerLon: parseFloat(document.getElementById('zc-lon').value),
      };
      if (!d.gridId) throw new Error('Grid ID required.');
      await API.createZone(d);
      msg.className = 'form-msg success'; msg.textContent = '✓ Zone created.';
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('ze-load').addEventListener('click', async () => {
    const id = document.getElementById('ze-id').value.trim();
    if (!id) return;
    try {
      const z = await API.getZone(id);
      document.getElementById('ze-lat').value = z.centerLat || '';
      document.getElementById('ze-lon').value = z.centerLon || '';
      document.getElementById('zone-edit-form').classList.remove('hidden');
    } catch (e) {
      document.getElementById('ze-msg').className = 'form-msg error';
      document.getElementById('ze-msg').textContent = '✗ ' + e.message;
    }
  });

  document.getElementById('ze-save').addEventListener('click', async () => {
    const id  = document.getElementById('ze-id').value.trim();
    const msg = document.getElementById('ze-msg');
    try {
      await API.updateZone(id, {
        gridId:    id,
        centerLat: parseFloat(document.getElementById('ze-lat').value),
        centerLon: parseFloat(document.getElementById('ze-lon').value),
      });
      msg.className = 'form-msg success'; msg.textContent = '✓ Updated.';
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('ze-delete').addEventListener('click', async () => {
    const id  = document.getElementById('ze-id').value.trim();
    const msg = document.getElementById('ze-msg');
    if (!confirm(`Delete zone "${id}"?`)) return;
    try {
      await API.deleteZone(id);
      msg.className = 'form-msg success'; msg.textContent = '✓ Deleted.';
      document.getElementById('zone-edit-form').classList.add('hidden');
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('recalibrate-btn').addEventListener('click', async () => {
    const msg = document.getElementById('recal-msg');
    msg.className = 'form-msg'; msg.textContent = 'Running…';
    try {
      const d = await API.recalibrate();
      msg.className = 'form-msg success'; msg.textContent = '✓ ' + (d.message || 'Started.');
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });
}

// ═══════════════════════════════════════════
// CSV DROP
// ═══════════════════════════════════════════
function initCSVDrop() {
  const drop  = document.getElementById('csv-drop');
  const input = document.getElementById('csv-input');
  const msg   = document.getElementById('csv-msg');
  if (!drop) return;
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag-over'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('drag-over'));
  drop.addEventListener('drop', e => {
    e.preventDefault(); drop.classList.remove('drag-over');
    if (e.dataTransfer.files.length) handleCSV(e.dataTransfer.files[0], msg);
  });
  input.addEventListener('change', () => { if (input.files.length) handleCSV(input.files[0], msg); });
}

async function handleCSV(file, msgEl) {
  msgEl.className = 'form-msg'; msgEl.textContent = 'Uploading…';
  try {
    const r = await API.importTelemetryCSV(file);
    msgEl.className = 'form-msg success';
    msgEl.textContent = `✓ Processed ${r.recordsProcessed} records, ${r.relationsCreated} relations.`;
  } catch (e) { msgEl.className = 'form-msg error'; msgEl.textContent = '✗ ' + e.message; }
}

// ═══════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════
function setStatus(msg) {
  const el = document.getElementById('map-status');
  if (el) el.textContent = msg;
}

// grid card click → jump to map + open drawer
function selectShark(sharkOrId) {
  if (!sharkOrId) return;

  let shark;
  // Jeśli przekazano string (ID), znajdź pełny obiekt w stanie aplikacji
  if (typeof sharkOrId === 'string') {
    shark = State.sharks.find(s => s.sharkId === sharkOrId || s.id === sharkOrId);
  } else {
    // Jeśli przekazano już gotowy obiekt, użyj go bezpośrednio
    shark = sharkOrId;
  }

  if (!shark) return;

  State.selectedShark = shark;
  State.selectedSharkTrajectory = null;

  // Usuń klasę active ze wszystkich typów kart (zarówno na sidebarze, jak i na siatce)
  document.querySelectorAll('.shark-card, .shark-grid-card').forEach(c => c.classList.remove('active'));

  // Znajdź kartę na pasku bocznym (sidebar) przy użyciu atrybutu data-id
  const sidebarCard = document.querySelector(`.shark-card[data-id="${shark.sharkId}"]`);
  if (sidebarCard) sidebarCard.classList.add('active');

  // Znajdź kartę na siatce (grid) przy użyciu atrybutu data-shark-id
  const gridCard = document.querySelector(`.shark-grid-card[data-shark-id="${shark.sharkId}"]`);
  if (gridCard) gridCard.classList.add('active');

  openDrawer(shark);
}

// grid card click → jump to map + open drawer
function selectSharkFromGrid(shark) {
  // Przełączenie widoku na mapę
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('[data-view="map"]').forEach(t => t.classList.add('active'));
  document.getElementById('view-map').classList.add('active');

  // Odczekaj na zmianę widoku w DOM, a następnie zaznacz rekina i przewiń pasek boczny
  setTimeout(() => {
    selectShark(shark);
    const sidebarCard = document.querySelector(`.shark-card[data-id="${shark.sharkId}"]`);
    if (sidebarCard) {
      sidebarCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, 100);
}

function triggerZoneRefresh() {
  const currentZone = document.getElementById('zfp-zone')?.value;
  const zonePanel = document.getElementById('zone-panel');
  if (currentZone && zonePanel && zonePanel.classList.contains('open')) {
    openZonePanel(currentZone);
  }
}

// ===========================================================================
// TRANSLATE ANALYTICS CLUSTERS TO MAP VIEW
// ===========================================================================
window.transferClustersToMap = function() {
  // 1. Pobieramy daty oraz DOKŁADNY LIMIT ustawiony przez użytkownika w Analytics
  const anaStart = document.getElementById('ana-start')?.value;
  const anaEnd   = document.getElementById('ana-end')?.value;
  const anaLimit = parseInt(document.getElementById('ana-limit')?.value) || 10;

  // 2. Pobieramy kontrolki kalendarzy znajdujące się w panelu klastrów na mapie
  const mapStartEl = document.getElementById('cfp-start');
  const mapEndEl   = document.getElementById('cfp-end');

  // 3. Synchronizujemy wartości pól czasowych panelu klastrów na mapie
  if (mapStartEl && mapEndEl && anaStart && anaEnd) {
    mapStartEl.value = anaStart;
    mapEndEl.value   = anaEnd;
  }

  // 4. Czyścimy starą warstwę klastrów z mapy, aby uniknąć nakładania się danych
  if (_clusterLayerGroup && State.map) {
    State.map.removeLayer(_clusterLayerGroup);
    _clusterLayerGroup = null;
  }

  // 5. MODYFIKACJA STANU: Aktywujemy klastry. Nie modyfikujemy stanu stref (State.showZones).
  State.showClusters = true;

  // Podświetlamy guzik sterujący na pasku mapy
  const ctrlClusters = document.getElementById('ctrl-clusters');
  if (ctrlClusters) {
    ctrlClusters.classList.add('active');
  }

  // Ukrywamy formularze z kalendarzami, aby nie zasłaniały widoku mapy
  document.getElementById('cluster-filter-panel')?.classList.add('hidden');
  document.getElementById('zone-filter-panel')?.classList.add('hidden');

  // 6. Przełączamy widok interfejsu (SPA) na zakładkę MAP
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('[data-view="map"]').forEach(t => t.classList.add('active'));
  document.getElementById('view-map').classList.add('active');

  // 7. Odpytujemy API o klastry, przekazując DOKŁADNIE TEN SAM LIMIT co w tabeli
  setTimeout(async () => {
    try {
      const start = (anaStart || '2000-01-01T00:00').replace('T', ' ') + ':00';
      const end   = (anaEnd   || '2030-12-31T23:59').replace('T', ' ') + ':00';

      const data = await API.getClusters(start, end, anaLimit);

      _clusterLayerGroup = L.layerGroup();

      if (data.clusters && data.clusters.length) {
        const maxPings = Math.max(...data.clusters.map(c => c.totalPings), 1);

        data.clusters.forEach(c => {
          const ratio = c.totalPings / maxPings;
          L.circleMarker([c.centerLat, c.centerLon], {
            radius: Math.round(14 + ratio * 22),
            fillColor: '#00e5c8',
            color: '#00e5c8',
            weight: 1,
            opacity: 0.3 + ratio * 0.5,
            fillOpacity: (0.3 + ratio * 0.5) * 0.35,
          }).bindPopup(`<strong>${c.gridId}</strong><br>Pings: ${c.totalPings}<br>Sharks: ${c.uniqueSharksCount}`)
            .addTo(_clusterLayerGroup);
        });

        if (State.showClusters) _clusterLayerGroup.addTo(State.map);
      }

      refreshMapLayers();
      State.map.setView([25, -50], 4);
    } catch (e) {
      setStatus('Cluster synchronization failed');
    }
  }, 150);
};

function syncMapToAnalyticsDates() {
  // Dla klastrów synchronizujemy panel klastrów (cfp)
  const mapStart = document.getElementById('cfp-start')?.value;
  const mapEnd   = document.getElementById('cfp-end')?.value;
  const anaStartEl = document.getElementById('ana-start');
  const anaEndEl   = document.getElementById('ana-end');
  if (anaStartEl && anaEndEl && mapStart && mapEnd) {
    anaStartEl.value = mapStart;
    anaEndEl.value   = mapEnd;
  }
}

function syncAnalyticsToMapDates() {
  const anaStart = document.getElementById('ana-start')?.value;
  const anaEnd   = document.getElementById('ana-end')?.value;
  const cfpStartEl = document.getElementById('cfp-start');
  const cfpEndEl   = document.getElementById('cfp-end');
  if (cfpStartEl && cfpEndEl && anaStart && anaEnd) {
    cfpStartEl.value = anaStart;
    cfpEndEl.value   = anaEnd;
  }
}
