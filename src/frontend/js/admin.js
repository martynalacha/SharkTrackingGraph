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

  document.getElementById('se-load').addEventListener('click', async () => {
    const id = document.getElementById('se-id').value.trim();
    if (!id) return;
    try {
      const s = await API.searchShark(id);
      document.getElementById('se-name').value    = s.name    || '';
      document.getElementById('se-species').value = s.species || '';
      document.getElementById('se-gender').value  = s.gender  || 'Unknown';
      document.getElementById('se-length').value  = s.length  || '';
      document.getElementById('se-weight').value  = s.weight  || '';
      document.getElementById('shark-edit-form').classList.remove('hidden');
    } catch (e) {
      const msg = document.getElementById('se-msg');
      msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message;
    }
  });

  document.getElementById('se-save').addEventListener('click', async () => {
    const id  = document.getElementById('se-id').value.trim();
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
    const id  = document.getElementById('se-id').value.trim();
    const msg = document.getElementById('se-msg');
    if (!confirm(`Delete shark "${id}"?`)) return;
    try {
      await API.deleteShark(id);
      msg.className = 'form-msg success'; msg.textContent = '✓ Deleted.';
      document.getElementById('shark-edit-form').classList.add('hidden');
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
      const msg = document.getElementById('ze-msg');
      msg.className = 'form-msg error'; msg.textContent = '✗ ' + e.message;
    }
  });

  document.getElementById('ze-save').addEventListener('click', async () => {
    const id  = document.getElementById('ze-id').value.trim();
    const msg = document.getElementById('ze-msg');
    try {
      await API.updateZone(id, {
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
