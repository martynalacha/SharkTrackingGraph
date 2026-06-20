/**
 * ui.js — SharkTrack rendering functions
 */

const UI = (() => {

  function genderSym(g) {
    if (!g) return '';
    const l = g.toLowerCase();
    if (l === 'male')   return '♂';
    if (l === 'female') return '♀';
    return '';
  }

  function thumbHTML(shark, size = 40) {
    if (shark.speciesImage) {
      return `<img class="shark-thumb" src="${shark.speciesImage}" alt=""
        style="width:${size}px;height:${size}px;"
        onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <div class="shark-thumb-placeholder" style="display:none;width:${size}px;height:${size}px;">🦈</div>`;
    }
    return `<div class="shark-thumb-placeholder" style="width:${size}px;height:${size}px;">🦈</div>`;
  }


// ── sidebar list ────────────────────────
  function renderSharkList(sharks) {
    const el = document.getElementById('shark-list');
    if (!el) return;

    if (!sharks.length) {
      el.innerHTML = '<div class="loading-msg">No sharks match filter.</div>';
      return;
    }

    el.innerHTML = sharks.map(s => {
      // Przekazujemy s.sharkId jako string do standardowej funkcji selectShark
      return `
      <div class="shark-card" data-id="${s.sharkId}" onclick="selectShark('${s.sharkId}')">
        ${thumbHTML(s, 40)}
        <div class="shark-info">
          <div class="shark-info-name">${s.name}</div>
          <div class="shark-info-species">${s.species || '—'}</div>
          <div class="shark-info-meta">${genderSym(s.gender)} ${s.length ? `${s.length}m` : ''} ${s.weight ? ` · ${s.weight}kg` : ''}</div>
        </div>
      </div>`;
    }).join('');
  }
  // ── species dropdowns ───────────────────
  function renderSpeciesOptions(sharks, selectId = 'filter-species') {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const species = [...new Set(sharks.map(s => s.species).filter(Boolean))].sort();
    const first = sel.options[0];
    sel.innerHTML = '';
    if (first) sel.appendChild(first);
    species.forEach(sp => {
      const opt = document.createElement('option');
      opt.value = sp; opt.textContent = sp;
      sel.appendChild(opt);
    });
  }



function buildDrawerHTML(shark) {
    const img = shark.speciesImage
    ? `<img class="drawer-image" src="${shark.speciesImage}" alt="${shark.name}" title="${shark.speciesImage}"
        onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <div class="drawer-image-placeholder" style="display:none;">🦈</div>`
    : `<div class="drawer-image-placeholder">🦈</div>`;

    const displayLength = shark.length ? `${shark.length} m` : '—';
    const displayWeight = shark.weight ? `${shark.weight} kg` : '—';
    return `
      ${img}
      <div class="drawer-info">
        <div class="drawer-name">${shark.name}</div>
        <div class="drawer-species">${shark.species || '—'}</div>
        <div class="drawer-stats">
          <div class="stat-box">
            <div class="stat-label">LENGTH</div>
            <div class="stat-value">${displayLength}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">WEIGHT</div>
            <div class="stat-value">${displayWeight}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">GENDER</div>
            <div class="stat-value">
              <span style="font-size: 20px; line-height: 1; font-weight: 800; font-family: sans-serif;">
                ${genderSym(shark.gender) || '—'}
              </span>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-label">ID</div>
            <div class="stat-value">${shark.sharkId || '—'}</div>
          </div>
        </div>
        <div class="traj-controls">
          <div class="traj-range">
            <label>FROM
              <input type="datetime-local" class="filter-input" id="traj-start" />
            </label>
            <label>TO
              <input type="datetime-local" class="filter-input" id="traj-end" />
            </label>
          </div>
          <button class="drawer-trajectory-btn" id="trajectory-btn">◉ SHOW TRAJECTORY</button>
        </div>
        <div class="trajectory-bar" id="trajectory-bar"></div>
      </div>`;
}
  // ── trajectory timeline ─────────────────
  function renderTrajectoryTimeline(trajectory) {
    const bar = document.getElementById('trajectory-bar');
    if (!bar) return;
    if (!trajectory.length) { bar.innerHTML = '<div class="loading-msg">No points.</div>'; return; }
    const slice = trajectory.slice(-14);
    bar.innerHTML = slice.map(p => `
      <div class="traj-item">
        <div class="traj-dot"></div>
        <span>${p.timestamp || '—'}</span>
        <span style="margin-left:auto;color:var(--accent);font-size:10px;">${p.zone || ''}</span>
      </div>`).join('');
  }

// ── zone panel ──────────────────────────
function buildZonePanelHTML(zone) {
    const sharks = zone.sharks || [];
    const sharksHTML = sharks.length
      ? sharks.map(s => `
          <div class="zone-shark-item">
            <span>${s.name || '—'}</span>
            <span style="color:var(--text-dim);font-size:10px;margin-left:6px;">${s.species || ''}</span>
          </div>`).join('')
      : '<div class="zone-shark-item" style="font-style:italic;">No detections in this period.</div>';

    const inputStart = document.getElementById('zfp-start')?.value || '';
    const inputEnd   = document.getElementById('zfp-end')?.value || '';

    const displayStart = inputStart.replace('T', ' ') || '—';
    const displayEnd   = inputEnd.replace('T', ' ') || '—';

    return `
      <div class="zone-title">⬡ ${zone.gridId}</div>
      <div class="zone-coords">${(zone.centerLat||0).toFixed(4)}, ${(zone.centerLon||0).toFixed(4)}</div>
      <div class="zone-stat">
        <span class="zone-stat-key">UNIQUE SHARKS</span>
        <span class="zone-stat-val">${sharks.length}</span>
      </div>
      <div class="zone-stat">
        <span class="zone-stat-key">FROM</span>
        <span class="zone-stat-val" style="font-size:10px;">${displayStart}</span>
      </div>
      <div class="zone-stat">
        <span class="zone-stat-key">TO</span>
        <span class="zone-stat-val" style="font-size:10px;">${displayEnd}</span>
      </div>
      <div class="zone-shark-list">
        <div style="font-size:9px;letter-spacing:.12em;color:var(--text-dim);margin:9px 0 5px;">DETECTIONS</div>
        ${sharksHTML}
      </div>
      <button class="zone-traj-btn" id="zone-traj-all-btn">◉ SHOW ALL TRAJECTORIES IN THIS ZONE</button>`;
  }

  // ── grid card (DOM element, for append) ──
function buildGridCard(s) {
    const div = document.createElement('div');
    div.className = 'shark-grid-card';


    div.setAttribute('data-shark-id', s.sharkId || s.id);

    div.onclick = function() {
      if (typeof selectSharkFromGrid === 'function') {
        selectSharkFromGrid(s);
      }
    };

    div.innerHTML = `
      ${s.speciesImage
        ? `<img class="shark-grid-img" src="${s.speciesImage}" alt="${s.name}"
              onerror="this.outerHTML='<div class=\\'shark-grid-img-placeholder\\'>🦈</div>'" />`
        : `<div class="shark-grid-img-placeholder">🦈</div>`}
      <div class="shark-grid-body">
        <div class="shark-grid-name">${s.name}</div>
        <div class="shark-grid-species">${s.species || '—'}</div>
        <div class="shark-grid-tags">
          ${ (s.gender && s.gender.toString().toLowerCase() !== 'nan')
            ? `<span class="tag tag-accent">${genderSym(s.gender)} ${s.gender}</span>`
            : ''
          }
          ${s.length ? `<span class="tag">${s.length} m</span>` : ''}
          ${s.weight ? `<span class="tag">${s.weight} kg</span>` : ''}
        </div>
      </div>`;
    return div;
  }
  // ── analytics ───────────────────────────
 function renderClusters(clusters) {
    const grid = document.getElementById('analytics-grid');
    if (!grid) return;

    if (!clusters.length) {
      grid.innerHTML = '<div class="loading-msg">No data for this period.</div>';
      return;
    }

    const maxPings = Math.max(...clusters.map(c => c.totalPings), 1);


    const cardsHTML = clusters.map((c, i) => `
      <div class="cluster-card">
        <div class="cluster-rank">#${i+1} HOT ZONE</div>
        <div class="cluster-id">${c.gridId}</div>
        <div class="cluster-ping-bar">
          <div class="cluster-ping-fill" style="width:${Math.round(c.totalPings/maxPings*100)}%"></div>
        </div>
        <div class="cluster-meta">PINGS <span>${c.totalPings}</span> &nbsp; SHARKS <span>${c.uniqueSharksCount}</span></div>
        <div style="font-size:9px;color:var(--text-dim);margin-top:5px;">${(c.centerLat||0).toFixed(4)}, ${(c.centerLon||0).toFixed(4)}</div>
      </div>`).join('');


    grid.innerHTML = `
      <div style="grid-column: 1 / -1; margin-bottom: 15px;">
        <button class="btn-primary" id="ana-show-on-map-btn" style="width:100%; background: var(--accent); color: var(--bg); font-weight: bold;">
          🗺 SHOW THIS TEMPORAL CLUSTER ON MAP
        </button>
      </div>
      ${cardsHTML}`;


    document.getElementById('ana-show-on-map-btn')?.addEventListener('click', () => {
      if (typeof window.transferClustersToMap === 'function') {
        window.transferClustersToMap();
      }
    });
  }
  function renderCentrality(results) {
    const grid = document.getElementById('centrality-grid');
    if (!results?.length) { grid.innerHTML = '<div class="loading-msg">No data.</div>'; return; }
    grid.innerHTML = results.map(r => `
      <div class="cent-card">
        <div>
          <div class="cent-id">${r.gridId}</div>
          <div style="font-size:9px;color:var(--text-dim);">${(r.centerLat||0).toFixed(3)}, ${(r.centerLon||0).toFixed(3)}</div>
        </div>
        <div class="cent-score">${r.centralityDegreeScore}</div>
      </div>`).join('');
  }

  return { renderSharkList, renderSpeciesOptions, buildDrawerHTML,
           renderTrajectoryTimeline, buildZonePanelHTML,
           buildGridCard, renderClusters, renderCentrality };
})();
