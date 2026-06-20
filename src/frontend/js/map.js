function initMap() {
  State.map = L.map('map', { center: [20, -30], zoom: 3 });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap', maxZoom: 18,
  }).addTo(State.map);

  document.getElementById('ctrl-zones').addEventListener('click', function () {
    State.showZones = !State.showZones;
    this.classList.toggle('active', State.showZones);
    const panel = document.getElementById('zone-filter-panel');
    if (State.showZones) {
      panel.classList.remove('hidden');
    } else {
      panel.classList.add('hidden');
      closeZonePanel();
      State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
      State.zoneTrajectoryLayers = [];
    }
    refreshMapLayers();
  });

  document.getElementById('ctrl-clusters').addEventListener('click', function () {
    State.showClusters = !State.showClusters;
    this.classList.toggle('active', State.showClusters);
    const clusterPanel = document.getElementById('cluster-filter-panel');
    if (State.showClusters) {
      clusterPanel.classList.remove('hidden');
      loadClusterMarkers();
    } else {
      clusterPanel.classList.add('hidden');
      refreshMapLayers();
    }
  });

  document.getElementById('zfp-close').addEventListener('click', () => {
    document.getElementById('zone-filter-panel').classList.add('hidden');
  });

  document.getElementById('cfp-close')?.addEventListener('click', () => {
    document.getElementById('cluster-filter-panel').classList.add('hidden');
  });

  document.getElementById('zfp-zone').addEventListener('change', function () {
    if (this.value) openZonePanel(this.value);
    else closeZonePanel();
    refreshMapLayers();
  });

  document.getElementById('zfp-start')?.addEventListener('input', triggerZoneRefresh);
  document.getElementById('zfp-end')?.addEventListener('input', triggerZoneRefresh);

  document.getElementById('cfp-start')?.addEventListener('input', () => {
    const val = document.getElementById('cfp-start').value;
    const el = document.getElementById('ana-start');
    if (el) el.value = val;
    loadClusterMarkers();
  });

  document.getElementById('cfp-end')?.addEventListener('input', () => {
    const val = document.getElementById('cfp-end').value;
    const el = document.getElementById('ana-end');
    if (el) el.value = val;
    loadClusterMarkers();
  });

  document.getElementById('drawer-close').addEventListener('click', closeDrawer);
  document.getElementById('zone-panel-close').addEventListener('click', closeZonePanel);
}

async function loadMapView() {
  await Promise.all([loadSharks(), loadZoneMarkers()]);
  populateZoneFilterDropdown();
}

async function loadZoneMarkers() {
  try {
    const markers = await API.getZoneMarkers();
    State.zoneMarkers = markers;

    const globalBounds = await API.getZoneBounds('ALL_ZONES');
    State.globalTimeBounds = {
      start: globalBounds.start.replace(' ', 'T').substring(0, 16),
      end:   globalBounds.end.replace(' ', 'T').substring(0, 16),
    };

    const startEl = document.getElementById('zfp-start');
    const endEl   = document.getElementById('zfp-end');
    if (startEl && endEl) {
      startEl.min = State.globalTimeBounds.start; startEl.max = State.globalTimeBounds.end;
      endEl.min   = State.globalTimeBounds.start; endEl.max   = State.globalTimeBounds.end;
      startEl.value = State.globalTimeBounds.start;
      endEl.value   = State.globalTimeBounds.end;
    }

    const anaStartEl = document.getElementById('ana-start');
    const anaEndEl   = document.getElementById('ana-end');
    if (anaStartEl && anaEndEl) {
      anaStartEl.min = State.globalTimeBounds.start; anaStartEl.max = State.globalTimeBounds.end;
      anaEndEl.min   = State.globalTimeBounds.start; anaEndEl.max   = State.globalTimeBounds.end;
      anaStartEl.value = State.globalTimeBounds.start;
      anaEndEl.value   = State.globalTimeBounds.end;
    }

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
    const currentGridId = m.gridId || m.zoneName;
    L.marker([m.lat, m.lon], { icon, gridId: currentGridId })
      .bindPopup(`<strong>${currentGridId || 'Zone'}</strong><br>Sharks: ${m.uniqueSharksCount || 0}`)
      .on('click', () => {
        const sel = document.getElementById('zfp-zone');
        if (sel) sel.value = currentGridId;
        openZonePanel(currentGridId);
        refreshMapLayers();
      })
      .addTo(_zoneLayerGroup);
  });
  if (State.showZones) _zoneLayerGroup.addTo(State.map);
}

function refreshMapLayers() {
  if (_zoneLayerGroup) {
    if (State.showZones) {
      const selectedZoneId = document.getElementById('zfp-zone')?.value;
      _zoneLayerGroup.eachLayer(layer => {
        const markerGridId = layer.options.gridId || layer.options.zoneName;
        if (!selectedZoneId || markerGridId === selectedZoneId) {
          if (!State.map.hasLayer(layer)) layer.addTo(State.map);
        } else {
          if (State.map.hasLayer(layer)) State.map.removeLayer(layer);
        }
      });
      if (!State.map.hasLayer(_zoneLayerGroup)) _zoneLayerGroup.addTo(State.map);
    } else {
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
    const start = document.getElementById('cfp-start')?.value || '2000-01-01T00:00';
    const end   = document.getElementById('cfp-end')?.value   || '2030-12-31T23:59';
    const data = await API.getClusters(start, end, 20);
    if (_clusterLayerGroup) State.map.removeLayer(_clusterLayerGroup);
    _clusterLayerGroup = L.layerGroup();
    if (!data.clusters?.length) return;
    const maxPings = Math.max(...data.clusters.map(c => c.totalPings), 1);
    data.clusters.forEach(c => {
      const ratio = c.totalPings / maxPings;
      L.circleMarker([c.centerLat, c.centerLon], {
        radius: Math.round(14 + ratio * 22),
        fillColor: '#00e5c8', color: '#00e5c8', weight: 1,
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

function populateZoneFilterDropdown() {
  const sel = document.getElementById('zfp-zone');
  State.zoneMarkers.forEach(m => {
    if (!m.zoneName) return;
    const opt = document.createElement('option');
    opt.value = m.zoneName; opt.textContent = m.zoneName;
    sel.appendChild(opt);
  });
}


function createTrajectoryLayer(traj, { color = '#00e5c8', sharkName = '' } = {}) {
  const pts = traj.filter(p => p.lat && p.lon).map(p => [p.lat, p.lon]);
  const line = L.polyline(pts, { color, weight: 2, opacity: 0.8 });
  const dots = traj.filter(p => p.lat && p.lon).map(p =>
    L.circleMarker([p.lat, p.lon], { radius: 3, color, fillColor: color, fillOpacity: 0.9, weight: 1 })
      .bindPopup(`<strong>${sharkName}</strong><br>${p.timestamp || ''}`)
  );
  return L.layerGroup([line, ...dots]);
}
