// ═══════════════════════════════════════
// ProductAI — Shared Frontend JS
// ═══════════════════════════════════════

const API = (()=>{
  // ── Change this to your Railway backend URL after deploying ──
  const BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://productai-backend.up.railway.app'; // UPDATE THIS

  const headers = (extra={}) => ({
    'Content-Type': 'application/json',
    ...(localStorage.getItem('token') ? {'Authorization': `Bearer ${localStorage.getItem('token')}`} : {}),
    ...extra
  });

  const req = async (method, path, body=null) => {
    const opts = { method, headers: headers() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(BASE + path, opts);
    const data = await res.json().catch(()=>({}));
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
  };

  return {
    BASE,
    get:    (path)       => req('GET',    path),
    post:   (path, body) => req('POST',   path, body),
    patch:  (path, body) => req('PATCH',  path, body),
    delete: (path)       => req('DELETE', path),

    // Auth
    register: (email,password,name) => req('POST','/api/auth/register',{email,password,name}),
    login:    (email,password)      => req('POST','/api/auth/login',{email,password}),
    me:       ()                    => req('GET', '/api/auth/me'),

    // Generate
    genEbook:     (d) => req('POST','/api/generate/ebook',d),
    genAudiobook: (d) => req('POST','/api/generate/audiobook',d),
    genVideo:     (d) => req('POST','/api/generate/video',d),
    genImages:    (d) => req('POST','/api/generate/images',d),
    genWebsite:   (d) => req('POST','/api/generate/website',d),
    genContent:   (d) => req('POST','/api/generate/content',d),
    genPrompts:   (d) => req('POST','/api/generate/prompts',d),
    genColoring:  (d) => req('POST','/api/generate/coloring-book',d),
    genCourse:    (d) => req('POST','/api/generate/course',d),
    taskStatus:   (id)=> req('GET', `/api/generate/status/${id}`),

    // Products
    myProducts: () => req('GET','/api/products/my'),
    delProduct: (id)=> req('DELETE',`/api/products/${id}`),

    // Payments
    checkout: (plan) => req('POST','/api/payments/checkout',{plan}),
    portal:   ()     => req('GET', '/api/payments/portal'),
    buyMarketplace: (product_id, price_cents) => req('POST','/api/payments/marketplace/buy',{product_id,price_cents}),

    // Marketplace
    marketplace: (category,page) => req('GET',`/api/marketplace/?${category?'category='+category+'&':''}page=${page||1}`),

    // User
    stats: () => req('GET','/api/user/stats'),
  };
})();

// ── Auth State ──
const Auth = {
  token: () => localStorage.getItem('token'),
  user:  () => { try { return JSON.parse(localStorage.getItem('user')||'null'); } catch{ return null; } },
  set:   (token, user) => { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)); },
  clear: () => { localStorage.removeItem('token'); localStorage.removeItem('user'); },
  isLoggedIn: () => !!localStorage.getItem('token'),
  requireAuth: () => { if (!Auth.isLoggedIn()) { window.location = 'login.html'; return false; } return true; },
  logout: () => { Auth.clear(); window.location = 'index.html'; }
};

// ── Toast ──
const Toast = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(msg, type='info', duration=3500) {
    this.init();
    const icons = { success:'✅', error:'❌', info:'ℹ️', warning:'⚠️' };
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span>${icons[type]||'•'}</span><span>${msg}</span>`;
    this.container.appendChild(el);
    setTimeout(() => { el.style.opacity='0'; el.style.transform='translateX(100%)'; el.style.transition='all .3s'; setTimeout(()=>el.remove(), 300); }, duration);
  },
  success: (m) => Toast.show(m,'success'),
  error:   (m) => Toast.show(m,'error'),
  info:    (m) => Toast.show(m,'info'),
};

// ── Modal ──
const Modal = {
  open(html, onClose) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `<div class="modal">${html}<button class="modal-close" onclick="Modal.close()">✕</button></div>`;
    overlay.addEventListener('click', e => { if (e.target === overlay) Modal.close(); });
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
    this._onClose = onClose;
    return overlay;
  },
  close() {
    document.querySelectorAll('.modal-overlay').forEach(el => el.remove());
    document.body.style.overflow = '';
    if (this._onClose) this._onClose();
  }
};

// ── Tabs ──
function initTabs(containerEl) {
  const container = containerEl || document;
  container.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.dataset.group;
      const target = btn.dataset.tab;
      container.querySelectorAll(`.tab-btn[data-group="${group}"]`).forEach(b => b.classList.remove('active'));
      container.querySelectorAll(`.tab-panel[data-group="${group}"]`).forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      container.querySelector(`.tab-panel[data-group="${group}"][data-tab="${target}"]`)?.classList.add('active');
    });
  });
}

// ── Poll task until done ──
async function pollTask(taskId, onProgress, onDone, onError, interval=1200) {
  const poll = async () => {
    try {
      const r = await API.taskStatus(taskId);
      if (r.status === 'done') { onDone(r.result); return; }
      if (r.status === 'failed') { onError(r.error || 'Generation failed'); return; }
      onProgress(r.pct || 0, r.step || 'Working...');
      setTimeout(poll, interval);
    } catch(e) { onError(e.message); }
  };
  poll();
}

// ── Nav: set active link ──
function setActiveNav() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });
}

// ── Update nav credits ──
async function refreshNav() {
  if (!Auth.isLoggedIn()) return;
  try {
    const u = Auth.user();
    const credEl = document.querySelector('.nav-credits');
    if (credEl && u) credEl.textContent = u.plan === 'agency' ? '∞ credits' : `${u.credits} credits`;
    const loginBtn = document.getElementById('nav-login');
    const logoutBtn = document.getElementById('nav-logout');
    const dashBtn = document.getElementById('nav-dashboard');
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = '';
    if (dashBtn) dashBtn.style.display = '';
  } catch {}
}

// ── Format bytes ──
function fmtBytes(b) {
  if (b < 1024) return b+'B';
  if (b < 1024*1024) return (b/1024).toFixed(1)+'KB';
  return (b/(1024*1024)).toFixed(1)+'MB';
}

// ── Copy to clipboard ──
async function copyText(text, btn) {
  await navigator.clipboard.writeText(text);
  const orig = btn?.textContent;
  if (btn) { btn.textContent = 'Copied!'; setTimeout(()=>btn.textContent=orig, 1500); }
  Toast.success('Copied to clipboard');
}

// ── Init on load ──
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  setActiveNav();
  refreshNav();
});
