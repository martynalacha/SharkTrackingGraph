async function pollRecalibrationStatus(msgEl, maxAttempts = 120) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    let status;
    try {
      status = await API.getRecalibrationStatus();
    } catch (e) {
      msgEl.className = 'form-msg error'; msgEl.textContent = '✗ ' + e.message;
      return;
    }

    if (status.status === 'done') {
      msgEl.className = 'form-msg success'; msgEl.textContent = '✓ Done.';
      await refreshAllData();
      return;
    }
    if (status.status === 'error') {
      msgEl.className = 'form-msg error'; msgEl.textContent = '✗ ' + (status.error || 'Recalibration failed.');
      return;
    }

    msgEl.className = 'form-msg'; msgEl.textContent = 'Running…';
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  msgEl.className = 'form-msg error'; msgEl.textContent = '✗ Timed out waiting for recalibration to finish.';
}

function populateSelect(selectEl, values, placeholder, extraOptionValue, extraOptionLabel) {
  const currentValue = selectEl.value;
  selectEl.innerHTML = '';
  const placeholderOpt = document.createElement('option');
  placeholderOpt.value = '';
  placeholderOpt.textContent = placeholder;
  selectEl.appendChild(placeholderOpt);
  values.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    selectEl.appendChild(opt);
  });
  if (extraOptionValue) {
    const opt = document.createElement('option');
    opt.value = extraOptionValue;
    opt.textContent = extraOptionLabel;
    selectEl.appendChild(opt);
  }
  const stillExists = Array.from(selectEl.options).some(o => o.value === currentValue);
  selectEl.value = stillExists ? currentValue : '';
}

function refreshSpeciesSelects(sharks) {
  const species = [...new Set((sharks || []).map(s => s.species).filter(Boolean))].sort();
  const scSel = document.getElementById('sc-species-select');
  const seSel = document.getElementById('se-species-select');
  if (scSel) populateSelect(scSel, species, 'Select species *', '__new__', '+ New species…');
  if (seSel) populateSelect(seSel, species, 'Select species', '__new__', '+ New species…');
}

function refreshSharkIdSelect(sharks) {
  const sel = document.getElementById('se-id');
  if (!sel) return;
  const ids = (sharks || []).map(s => s.sharkId).filter(Boolean).sort();
  populateSelect(sel, ids, 'Select shark…');
}

function refreshZoneIdSelect(zoneMarkers) {
  const sel = document.getElementById('ze-id');
  if (!sel) return;
  const ids = (zoneMarkers || []).map(m => m.gridId || m.zoneName).filter(Boolean).sort();
  populateSelect(sel, ids, 'Select zone…');
}

function wireSpeciesCombobox(selectId, inputId) {
  const select = document.getElementById(selectId);
  const input = document.getElementById(inputId);
  if (!select || !input) return;
  select.addEventListener('change', () => {
    if (select.value === '__new__') {
      input.classList.remove('hidden');
      input.value = '';
      input.focus();
    } else {
      input.classList.add('hidden');
      input.value = select.value;
    }
  });
}

function getSpeciesValue(selectId, inputId) {
  const select = document.getElementById(selectId);
  const input = document.getElementById(inputId);
  if (select.value === '__new__') return input.value.trim();
  return select.value;
}

async function loadSharkIntoEditForm() {
  const id = document.getElementById('se-id').value.trim();
  if (!id) return;
  try {
    const s = await API.searchShark(id);
    document.getElementById('se-name').value = s.name || '';
    const seSel = document.getElementById('se-species-select');
    const seInput = document.getElementById('se-species');
    const hasSpecies = Array.from(seSel.options).some(o => o.value === s.species);
    if (hasSpecies) {
      seSel.value = s.species || '';
      seInput.classList.add('hidden');
      seInput.value = s.species || '';
    } else {
      seSel.value = '__new__';
      seInput.classList.remove('hidden');
      seInput.value = s.species || '';
    }
    document.getElementById('se-gender').value = s.gender || 'Unknown';
    document.getElementById('se-length').value = s.length || '';
    document.getElementById('se-weight').value = s.weight || '';
    document.getElementById('shark-edit-form').classList.remove('hidden');
    document.getElementById('se-msg').textContent = '';
  } catch (e) {
    const msg = document.getElementById('se-msg');
    msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message;
  }
}

async function loadZoneIntoEditForm() {
  const id = document.getElementById('ze-id').value.trim();
  if (!id) return;
  try {
    const z = await API.getZone(id);
    document.getElementById('ze-lat').value = z.centerLat || '';
    document.getElementById('ze-lon').value = z.centerLon || '';
    document.getElementById('zone-edit-form').classList.remove('hidden');
    document.getElementById('ze-msg').textContent = '';
  } catch (e) {
    const msg = document.getElementById('ze-msg');
    msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message;
  }
}

async function refreshAdminFormOptions() {
  let sharks = State.sharks;
  if (!sharks || !sharks.length) {
    try { sharks = await API.getSharks(); State.sharks = sharks; } catch (e) { sharks = []; }
  }
  let zoneMarkers = State.zoneMarkers;
  if (!zoneMarkers || !zoneMarkers.length) {
    try { zoneMarkers = await API.getZoneMarkers(); State.zoneMarkers = zoneMarkers; } catch (e) { zoneMarkers = []; }
  }
  refreshSpeciesSelects(sharks);
  refreshSharkIdSelect(sharks);
  refreshZoneIdSelect(zoneMarkers);
}

function initAdminHandlers() {
  refreshAdminFormOptions();
  wireSpeciesCombobox('sc-species-select', 'sc-species');
  wireSpeciesCombobox('se-species-select', 'se-species');

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
        refreshAdminFormOptions();
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

  document.getElementById('sc-submit').addEventListener('click', async () => {
    const msg = document.getElementById('sc-msg');
    try {
      const d = {
        sharkId: document.getElementById('sc-id').value.trim(),
        name:    document.getElementById('sc-name').value.trim(),
        species: getSpeciesValue('sc-species-select', 'sc-species'),
        gender:  document.getElementById('sc-gender').value,
        length:  parseFloat(document.getElementById('sc-length').value),
        weight:  parseFloat(document.getElementById('sc-weight').value),
      };
      if (!d.sharkId || !d.name || !d.species) throw new Error('Fill required fields.');
      await API.createShark(d);
      msg.className = 'form-msg success'; msg.textContent = '✓ Shark created.';
      refreshAllData();
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('se-id').addEventListener('change', loadSharkIntoEditForm);
  document.getElementById('se-load').addEventListener('click', loadSharkIntoEditForm);

  document.getElementById('se-save').addEventListener('click', async () => {
    const id  = document.getElementById('se-id').value.trim();
    const msg = document.getElementById('se-msg');
    try {
      await API.updateShark(id, {
        name:    document.getElementById('se-name').value.trim(),
        species: getSpeciesValue('se-species-select', 'se-species'),
        gender:  document.getElementById('se-gender').value,
        length:  parseFloat(document.getElementById('se-length').value),
        weight:  parseFloat(document.getElementById('se-weight').value),
      });
      msg.className = 'form-msg success'; msg.textContent = '✓ Updated.';
      refreshAllData();
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('se-delete').addEventListener('click', async () => {
    const id  = document.getElementById('se-id').value.trim();
    const msg = document.getElementById('se-msg');
    if (!confirm(`Delete shark "${id}"?`)) return;
    try {
      await API.deleteShark(id);
      msg.className = 'form-msg success'; msg.textContent = '✓ Deleted.';
      document.getElementById('shark-edit-form').classList.add('hidden');
      refreshAllData();
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

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
      refreshAllData();
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('ze-id').addEventListener('change', loadZoneIntoEditForm);
  document.getElementById('ze-load').addEventListener('click', loadZoneIntoEditForm);

  document.getElementById('ze-save').addEventListener('click', async () => {
    const id  = document.getElementById('ze-id').value.trim();
    const msg = document.getElementById('ze-msg');
    try {
      await API.updateZone(id, {
        centerLat: parseFloat(document.getElementById('ze-lat').value),
        centerLon: parseFloat(document.getElementById('ze-lon').value),
      });
      msg.className = 'form-msg success'; msg.textContent = '✓ Updated.';
      refreshAllData();
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
      refreshAllData();
    } catch (e) { msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message; }
  });

  document.getElementById('recalibrate-btn').addEventListener('click', async () => {
    const btn = document.getElementById('recalibrate-btn');
    const msg = document.getElementById('recal-msg');
    msg.className = 'form-msg'; msg.textContent = 'Running…';
    btn.disabled = true;
    try {
      await API.recalibrate();
      await pollRecalibrationStatus(msg);
    } catch (e) {
      msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message;
    } finally {
      btn.disabled = false;
    }
  });
}

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
    refreshAllData();
  } catch (e) { msgEl.className = 'form-msg error'; msgEl.textContent = '✗ ' + e.message; }
}
