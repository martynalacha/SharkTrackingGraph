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
