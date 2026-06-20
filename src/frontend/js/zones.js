async function openZonePanel(gridId) {
  if (!gridId) return;

  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];

  const panel = document.getElementById('zone-panel');
  document.getElementById('zone-panel-content').innerHTML = '<div class="loading-msg">Loading zone…</div>';
  panel.classList.add('open');

  const startEl = document.getElementById('zfp-start');
  const endEl   = document.getElementById('zfp-end');
  const isNewZone = startEl && startEl.getAttribute('data-current-zone') !== gridId;

  try {
    if (isNewZone && startEl && endEl) {
      const bounds = await API.getZoneBounds(gridId);
      const apiMin = bounds.start.replace(' ', 'T').substring(0, 16);
      const apiMax = bounds.end.replace(' ', 'T').substring(0, 16);
      startEl.min = apiMin; startEl.max = apiMax;
      endEl.min   = apiMin; endEl.max   = apiMax;
      startEl.value = apiMin;
      endEl.value   = apiMax;
      startEl.setAttribute('data-current-zone', gridId);
    }

    const startParam = startEl?.value || null;
    const endParam   = endEl?.value   || null;
    const data = await API.getZone(gridId, startParam, endParam);
    document.getElementById('zone-panel-content').innerHTML = UI.buildZonePanelHTML(data);

    const trajBtn = document.getElementById('zone-traj-all-btn');
    trajBtn?.addEventListener('click', () => {
      if (State.zoneTrajectoryLayers.length > 0) {
        State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
        State.zoneTrajectoryLayers = [];
        trajBtn.textContent = '◉ SHOW ALL TRAJECTORIES IN THIS ZONE';
        trajBtn.style.background  = 'rgba(0, 229, 200, 0.08)';
        trajBtn.style.color       = 'var(--accent)';
        trajBtn.style.borderColor = 'rgba(0, 229, 200, 0.3)';
      } else {
        runZoneTrajectoryFilter();
      }
    });
  } catch (e) {
    document.getElementById('zone-panel-content').innerHTML = '<div class="loading-msg">Zone processing failed.</div>';
  }
}

function closeZonePanel() {
  const panel = document.getElementById('zone-panel');
  if (panel) panel.classList.remove('open');

  const sel = document.getElementById('zfp-zone');
  if (sel) sel.value = '';

  const startEl = document.getElementById('zfp-start');
  const endEl   = document.getElementById('zfp-end');
  if (startEl && endEl) {
    startEl.removeAttribute('data-current-zone');
    const gMin = State.globalTimeBounds?.start || '2018-01-01T00:00';
    const gMax = State.globalTimeBounds?.end   || '2026-12-31T23:59';
    startEl.min = gMin; startEl.max = gMax;
    endEl.min   = gMin; endEl.max   = gMax;
    startEl.value = gMin;
    endEl.value   = gMax;
  }

  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];
  refreshMapLayers();
}

function triggerZoneRefresh() {
  const currentZone = document.getElementById('zfp-zone')?.value;
  const zonePanel   = document.getElementById('zone-panel');
  if (currentZone && zonePanel?.classList.contains('open')) openZonePanel(currentZone);
}

async function runZoneTrajectoryFilter() {
  const gridId = document.getElementById('zfp-zone').value;
  if (!gridId) return;

  State.zoneTrajectoryLayers.forEach(l => State.map.removeLayer(l));
  State.zoneTrajectoryLayers = [];

  const startParam = document.getElementById('zfp-start')?.value || null;
  const endParam   = document.getElementById('zfp-end')?.value   || null;

  try {
    const sharksTrajectories = await API.getZoneTrajectories(gridId, startParam, endParam);
    if (!sharksTrajectories.length) return;

    const COLORS = ['#00e5c8','#0099ff','#ff6b35','#a855f7','#f59e0b','#ec4899','#22c55e','#ef4444'];
    const getColor = i => i < COLORS.length ? COLORS[i] : `hsl(${(i * 137.5) % 360}, 70%, 60%)`;

    const bounds = [];
    sharksTrajectories.forEach((sharkData, i) => {
      const traj = sharkData.trajectory || [];
      if (!traj.length) return;
      const layer = createTrajectoryLayer(traj, {
        color: getColor(i),
        sharkName: sharkData.name || sharkData.sharkId,
      }).addTo(State.map);
      State.zoneTrajectoryLayers.push(layer);
      traj.forEach(p => bounds.push([p.lat, p.lon]));
    });

    if (bounds.length) State.map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });

    const trajBtn = document.getElementById('zone-traj-all-btn');
    setZoneTrajBtnToHide(trajBtn);
  } catch (e) {
    setStatus('Zone trajectory load failed');
  }
}

function setZoneTrajBtnToHide(btn) {
  if (!btn) return;
  btn.textContent      = '✕ HIDE ALL TRAJECTORIES';
  btn.style.background  = 'rgba(255, 62, 94, 0.08)';
  btn.style.color       = 'var(--danger)';
  btn.style.borderColor = 'rgba(255, 62, 94, 0.3)';
}
