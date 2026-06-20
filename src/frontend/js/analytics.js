function initAnalyticsHandlers() {
  document.getElementById('ana-run').addEventListener('click', runAnalysis);
}

async function runAnalysis() {
  const start = document.getElementById('ana-start').value || '2000-01-01T00:00';
  const end   = document.getElementById('ana-end').value   || '2030-12-31T23:59';
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

window.transferClustersToMap = function () {
  const anaStart = document.getElementById('ana-start')?.value;
  const anaEnd   = document.getElementById('ana-end')?.value;
  const anaLimit = parseInt(document.getElementById('ana-limit')?.value) || 10;

  const mapStartEl = document.getElementById('cfp-start');
  const mapEndEl   = document.getElementById('cfp-end');
  if (mapStartEl && mapEndEl && anaStart && anaEnd) {
    mapStartEl.value = anaStart;
    mapEndEl.value   = anaEnd;
  }

  if (_clusterLayerGroup && State.map) { State.map.removeLayer(_clusterLayerGroup); _clusterLayerGroup = null; }
  State.showClusters = true;
  document.getElementById('ctrl-clusters')?.classList.add('active');
  document.getElementById('cluster-filter-panel')?.classList.add('hidden');
  document.getElementById('zone-filter-panel')?.classList.add('hidden');

  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('[data-view="map"]').forEach(t => t.classList.add('active'));
  document.getElementById('view-map').classList.add('active');

  setTimeout(async () => {
    try {
      const start = anaStart || '2000-01-01T00:00';
      const end   = anaEnd   || '2030-12-31T23:59';
      const data  = await API.getClusters(start, end, anaLimit);
      _clusterLayerGroup = L.layerGroup();
      if (data.clusters?.length) {
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
      }
      refreshMapLayers();
      State.map.setView([25, -50], 4);
    } catch (e) {
      setStatus('Cluster synchronization failed');
    }
  }, 150);
};
