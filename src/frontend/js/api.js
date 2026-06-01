/**
 * api.js — SharkTrack API client
 * All backend calls go through here. Auth credentials stored in module scope.
 */

const API = (() => {
  let _adminUser = '';
  let _adminPass = '';

  function _authHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Basic ' + btoa(_adminUser + ':' + _adminPass)
    };
  }

  function setCredentials(user, pass) {
    _adminUser = user;
    _adminPass = pass;
  }

  // ─── PUBLIC ───────────────────────────────────

  async function getSharks(species = '') {
    const url = species
      ? `/api/sharks/?species=${encodeURIComponent(species)}`
      : '/api/sharks/';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch sharks');
    return res.json();
  }

  async function searchShark(q) {
    const res = await fetch(`/api/sharks/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error('Shark not found');
    return res.json();
  }

  async function getTrajectory(sharkId) {
    const res = await fetch(`/api/sharks/${encodeURIComponent(sharkId)}/trajectory`);
    if (!res.ok) throw new Error('Trajectory not found');
    return res.json();
  }

  async function getZoneMarkers() {
    const res = await fetch('/api/zones/markers');
    if (!res.ok) throw new Error('Failed to fetch markers');
    return res.json();
  }

  async function getZone(gridId, start, end) {
    let url = `/api/zones/${encodeURIComponent(gridId)}`;
    if (start && end) url += `?start_time=${encodeURIComponent(start)}&end_time=${encodeURIComponent(end)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Zone not found');
    return res.json();
  }

  async function getZoneBounds(gridId) {
    const res = await fetch(`/api/zones/${encodeURIComponent(gridId)}/bounds`);
    if (!res.ok) throw new Error('Zone bounds not found');
    return res.json();
  }

  async function getClusters(start, end, limit = 10) {
    const res = await fetch(
      `/api/zones/analysis/clusters?start_time=${encodeURIComponent(start)}&end_time=${encodeURIComponent(end)}&limit=${limit}`
    );
    if (!res.ok) throw new Error('Clusters fetch failed');
    return res.json();
  }

  async function getDegreeCentrality(limit = 10) {
    const res = await fetch(`/api/zones/analysis/degree-centrality?limit=${limit}`);
    if (!res.ok) throw new Error('Centrality fetch failed');
    return res.json();
  }

  // ─── ADMIN ────────────────────────────────────

  async function verifyAdmin(user, pass) {
    // Use a lightweight admin-only endpoint to test creds
    const res = await fetch('/api/admin/sharks/', {
      method: 'GET',
      headers: { 'Authorization': 'Basic ' + btoa(user + ':' + pass) }
    });
    return res.status !== 401;
  }

  async function createShark(data) {
    const res = await fetch('/api/admin/sharks/', {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(data)
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Create failed');
    return json;
  }

  async function updateShark(sharkId, data) {
    const res = await fetch(`/api/admin/sharks/${encodeURIComponent(sharkId)}`, {
      method: 'PUT',
      headers: _authHeaders(),
      body: JSON.stringify(data)
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Update failed');
    return json;
  }

  async function deleteShark(sharkId) {
    const res = await fetch(`/api/admin/sharks/${encodeURIComponent(sharkId)}`, {
      method: 'DELETE',
      headers: _authHeaders()
    });
    if (!res.ok) {
      const json = await res.json();
      throw new Error(json.detail || 'Delete failed');
    }
    return true;
  }

  async function createZone(data) {
    const res = await fetch('/api/admin/zones/', {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(data)
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Zone create failed');
    return json;
  }

  async function updateZone(gridId, data) {
    const res = await fetch(`/api/admin/zones/${encodeURIComponent(gridId)}`, {
      method: 'PUT',
      headers: _authHeaders(),
      body: JSON.stringify(data)
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Zone update failed');
    return json;
  }

  async function deleteZone(gridId) {
    const res = await fetch(`/api/admin/zones/${encodeURIComponent(gridId)}`, {
      method: 'DELETE',
      headers: _authHeaders()
    });
    if (!res.ok) {
      const json = await res.json();
      throw new Error(json.detail || 'Zone delete failed');
    }
    return true;
  }

  async function importTelemetryCSV(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/admin/sharks/import/telemetry', {
      method: 'POST',
      headers: { 'Authorization': 'Basic ' + btoa(_adminUser + ':' + _adminPass) },
      body: form
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Import failed');
    return json;
  }

  async function recalibrate() {
    const res = await fetch('/api/admin/recalibrate', {
      method: 'POST',
      headers: _authHeaders()
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Recalibration failed');
    return json;
  }

  async function getZoneBounds(gridId) {
    const res = await fetch(`/api/zones/${encodeURIComponent(gridId)}/bounds`);
    if (!res.ok) throw new Error('Zone bounds not found');
    return res.json();
  }

  // NOWA FUNKCJA DO POBIERANIA TRAJEKTORII STREFOWYCH
  async function getZoneTrajectories(gridId, start, end) {
    let url = `/api/zones/${encodeURIComponent(gridId)}/trajectories`;
    if (start && end) url += `?start_time=${encodeURIComponent(start)}&end_time=${encodeURIComponent(end)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch zone trajectories');
    return res.json();
  }

  async function loadClusterMarkers() {
  try {
    // Bezpieczne parsowanie formatu HTML: zastępujemy 'T' spacją i dodajemy sekundy
    const start = (State.globalTimeBounds?.start || '2000-01-01T00:00').replace('T', ' ') + ':00';
    const end   = (State.globalTimeBounds?.end   || '2030-12-31T23:59').replace('T', ' ') + ':00';

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



  return {
    setCredentials,
    getSharks,
    searchShark,
    getTrajectory,
    getZoneMarkers,
    getZone,
    getZoneBounds,
    getClusters,
    getDegreeCentrality,
    verifyAdmin,
    createShark,
    updateShark,
    deleteShark,
    createZone,
    updateZone,
    deleteZone,
    importTelemetryCSV,
    recalibrate,
    getZoneTrajectories
  };
})();
