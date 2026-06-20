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

function selectShark(sharkOrId) {
  if (!sharkOrId) return;
  const shark = typeof sharkOrId === 'string'
    ? State.sharks.find(s => s.sharkId === sharkOrId || s.id === sharkOrId)
    : sharkOrId;
  if (!shark) return;

  State.selectedShark = shark;
  State.selectedSharkTrajectory = null;

  document.querySelectorAll('.shark-card, .shark-grid-card').forEach(c => c.classList.remove('active'));
  document.querySelector(`.shark-card[data-id="${shark.sharkId}"]`)?.classList.add('active');
  document.querySelector(`.shark-grid-card[data-shark-id="${shark.sharkId}"]`)?.classList.add('active');
  openDrawer(shark);
}

function selectSharkFromGrid(shark) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('[data-view="map"]').forEach(t => t.classList.add('active'));
  document.getElementById('view-map').classList.add('active');
  setTimeout(() => {
    selectShark(shark);
    document.querySelector(`.shark-card[data-id="${shark.sharkId}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);
}

function openDrawer(shark) {
  document.getElementById('drawer-content').innerHTML = UI.buildDrawerHTML(shark);
  document.getElementById('shark-drawer').classList.add('open');
  wireDrawerButtons(shark);
}

function wireDrawerButtons(shark) {
  fetchTrajectoryMeta(shark.sharkId);
  document.getElementById('trajectory-btn')?.addEventListener('click', () => {
    applyTrajectoryFilter(shark.sharkId);
  });
}

async function fetchTrajectoryMeta(sharkId) {
  try {
    const data = await API.getTrajectory(sharkId);
    State.selectedSharkTrajectory = data;
    if (data.trajectory?.length) {
      const ts = data.trajectory.map(p => p.timestamp).filter(Boolean).sort();
      const startEl = document.getElementById('traj-start');
      const endEl   = document.getElementById('traj-end');
      if (startEl && endEl && ts.length) {
        startEl.min = startEl.value = toDatetimeLocal(ts[0]);
        startEl.max = toDatetimeLocal(ts[ts.length - 1]);
        endEl.min   = toDatetimeLocal(ts[0]);
        endEl.max   = endEl.value = toDatetimeLocal(ts[ts.length - 1]);
      }
    }
  } catch (_) {}
}

function toDatetimeLocal(ts) {
  if (!ts) return '';
  return ts.replace(' ', 'T').substring(0, 16);
}

async function applyTrajectoryFilter(sharkId) {
  const btn = document.getElementById('trajectory-btn');

  if (State.trajectoryLayer && btn?.textContent.includes('HIDE')) {
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
    let data = State.selectedSharkTrajectory || await API.getTrajectory(sharkId);
    let traj = data.trajectory || [];

    if (startVal && endVal) {
      const s = startVal.replace('T', ' ') + ':00';
      const e = endVal.replace('T', ' ')   + ':59';
      traj = traj.filter(p => !p.timestamp || (p.timestamp >= s && p.timestamp <= e));
    }

    if (!traj.length) throw new Error('No points in selected range');

    if (State.trajectoryLayer) State.map.removeLayer(State.trajectoryLayer);

    State.trajectoryLayer = createTrajectoryLayer(traj, {
      color: '#00e5c8',
      sharkName: State.selectedShark?.name || 'Shark',
    }).addTo(State.map);

    const line = State.trajectoryLayer.getLayers()[0];
    if (line?.getBounds) State.map.fitBounds(line.getBounds(), { padding: [40, 40] });

    UI.renderTrajectoryTimeline(traj);

    if (btn) { btn.textContent = '✕ HIDE TRAJECTORY'; btn.disabled = false; btn.classList.add('btn-active-hide'); }
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

async function initSharksView() {
  const area = document.getElementById('sharks-scroll-area');
  area.scrollTop = 0;
  State.gridPage = 0;
  const grid = document.getElementById('shark-grid');
  grid.innerHTML = '<div class="loading-msg">Loading…</div>';
  try {
    if (!State.sharks.length) State.sharks = await API.getSharks();
    State.gridFiltered = [...State.sharks];
    UI.renderSpeciesOptions(State.sharks, 'table-species');
    setupTableFilters();
    setupGridClick();
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
    el.setAttribute('data-shark-id', s.sharkId || s.id);
    grid.appendChild(el);
  });
  State.gridPage++;
}

function initGridInfiniteScroll() {
  const sentinel = document.getElementById('load-sentinel');
  if (!sentinel) return;
  if (window.sharkGridObserver) window.sharkGridObserver.disconnect();
  window.sharkGridObserver = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      if (State.gridPage * State.gridPageSize < State.gridFiltered.length) renderNextGridPage();
    }
  }, { rootMargin: '200px' });
  window.sharkGridObserver.observe(sentinel);
}

function setupTableFilters() {
  const search  = document.getElementById('table-search');
  const species = document.getElementById('table-species');
  function filter() {
    const q = document.getElementById('table-search').value.toLowerCase();
    const s = document.getElementById('table-species').value.toLowerCase();
    State.gridFiltered = State.sharks.filter(sh => {
      const mQ = !q || sh.name.toLowerCase().includes(q) || (sh.sharkId || '').toLowerCase().includes(q);
      const mS = !s || (sh.species || '').toLowerCase().includes(s);
      return mQ && mS;
    });
    renderNextGridPage(true);
  }
  const ns  = search.cloneNode(true);  search.parentNode.replaceChild(ns, search);
  const nsp = species.cloneNode(true); species.parentNode.replaceChild(nsp, species);
  ns.addEventListener('input', filter);
  nsp.addEventListener('change', filter);
}

function setupGridClick() {
  const grid = document.getElementById('shark-grid');
  grid.removeEventListener('click', handleGridClick);
  grid.addEventListener('click', handleGridClick);
}

function handleGridClick(e) {
  const card = e.target.closest('[data-shark-id]');
  if (!card) return;
  const shark = State.sharks.find(s => s.sharkId === card.getAttribute('data-shark-id'));
  if (shark) selectSharkFromGrid(shark);
}
