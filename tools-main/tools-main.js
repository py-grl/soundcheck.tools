const TOOLS = [
  { id: 'noke',       name: 'Noke',           icon: '🔐', url: 'https://smartentry.noke.com/v202511/#/app/facilities/facility/3267', accessIndex: 0 },
  { id: 'dock',       name: 'Dock Scheduler', icon: '📦', url: 'https://soundcheck.tools/dockscheduler/', accessIndex: 1 },
  { id: 'checkout',   name: 'Checkout',        icon: '✅', url: 'https://www.soundcheckout.com:8050/StudioCalendar2.aspx', accessIndex: 2 },
  { id: 'portalsT',  name: 'Package Tracking Portal',  icon: '🫆', url: 'https://www.trackinthecloud.com/mysoundchecknashville/Signin.aspx?ReturnUrl=/mysoundchecknashville/default.aspx', accessIndex: 3, row: 'portals-tracking' },
  { id: 'portalsN',  name: 'Tracking Number Search',  icon: '🔎', url: 'https://www.trackinthecloud.com/soundchecknashville/', accessIndex: 3, row: 'portals-tracking' },
  { id: 'portalsM',  name: 'Maintenance Portal',  icon: '⛑️', url: 'https://app.getmaintainx.com/request-portal/5c6458b3-da32-4b29-810b-425c49d7be0b', accessIndex: 3 },
  { id: 'parking',    name: 'Parking',         icon: '🅿', url: 'https://soundcheck.tools/parking', accessIndex: 4 },
  { id: 'noke2excel', name: 'Noke2Excel',      icon: '📊', url: 'https://soundcheck.tools/lockers/', accessIndex: 5 },
  { id: 'sharepoint', name: 'Sharepoint',      icon: '📃', url: 'https://clairglobal.sharepoint.com/sites/RockGlobalTeamInfo', accessIndex: 6 },
  { id: 'community', name: 'Rock.Community',      icon: '💛', url: 'https://www.rock.community/feed', accessIndex: 7 },
  { id: 'admin',      name: 'Admin',           icon: '⚙️', url: '/admin', accessIndex: 8, adminOnly: true }
];

function openTool(id) {
  const tool = TOOLS.find(t => t.id === id);
  if (!tool || !tool.url) return;
  if (tool.id === 'admin') { window.location.href = tool.url; } else { window.open(tool.url, '_blank'); }
}

function setUser(name) {
  document.getElementById('user-greeting').textContent = name || '';
  document.getElementById('logout-btn').style.display = name ? '' : 'none';
}

async function logout() {
  await fetch('/auth/logout', { method: 'POST' });
  setUser(null);
  document.getElementById('login-overlay').classList.remove('hidden');
}

// Consecutive tools sharing the same `row` key render together in one
// row-group (e.g. Package Tracking + Tracking Number Search); everything
// else — including tools that share an accessIndex but no `row`, like
// Maintenance Portal — gets its own full row.
function groupTools(tools) {
  const groups = [];
  for (const t of tools) {
    const key = t.row || t.id;
    const last = groups[groups.length - 1];
    if (last && last.key === key) last.items.push(t);
    else groups.push({ key, items: [t] });
  }
  return groups.map(g => g.items);
}

function miniCardHTML(t, numHTML = '') {
  const clickable = t.url ? `onclick="openTool('${t.id}')" role="button" tabindex="0" onkeydown="if(event.key==='Enter')openTool('${t.id}')"` : '';
  return `<div class="tool-mini-card" ${clickable}>
    ${numHTML}
    <div class="tool-icon">${t.icon}</div>
    <div class="tool-name">${t.name}</div>
  </div>`;
}

function render(isAdmin, access) {
  const visible = TOOLS.filter(t => access && access[t.accessIndex]);
  const groups = groupTools(visible);
  document.getElementById('tools-list').innerHTML = groups.map((group, i) => {
    if (group.length > 1) {
      const cards = group.map((t, idx) => miniCardHTML(t, idx === 0 ? `<div class="tool-num">0${i+1}</div>` : '')).join('');
      return `<div class="tool-row-group">${cards}</div>`;
    }
    const t = group[0];
    const clickable = t.url ? `onclick="openTool('${t.id}')" role="button" tabindex="0" onkeydown="if(event.key==='Enter')openTool('${t.id}')"` : '';
    return `<div class="tool-row" ${clickable}>
      <div class="tool-num">0${i+1}</div>
      <div class="tool-icon">${t.icon}</div>
      <div class="tool-name">${t.name}</div>
      <div class="tool-url ${t.url ? 'set' : ''}">${t.id === 'admin' ? 'soundcheck.tools/admin' : (t.url || 'Coming soon')}</div>
      <div class="tool-arrow">&#8599;</div>
    </div>`;
  }).join('');
}

function switchLoginTab(tab) {
  document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('form-signup').classList.toggle('hidden', tab !== 'signup');
  document.querySelectorAll('.login-tab').forEach((t, i) => t.classList.toggle('active', (i === 0) === (tab === 'login')));
  document.getElementById('login-error').classList.remove('show');
  document.getElementById('signup-error').classList.remove('show');
}

async function handleLogin(e) {
  e.preventDefault();
  const err = document.getElementById('login-error');
  err.classList.remove('show');
  try {
    const res = await fetch('/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: document.getElementById('login-email').value, password: document.getElementById('login-password').value })
    });
    const data = await res.json();
    if (!res.ok) { err.textContent = data.error || 'Login failed.'; err.classList.add('show'); return; }
    document.getElementById('login-overlay').classList.add('hidden');
    setUser(data.name);
    render(data.role === 'admin', data.access);
  } catch (e) {
    err.textContent = 'Could not reach server.'; err.classList.add('show');
  }
}

async function handleSignup(e) {
  e.preventDefault();
  const pw = document.getElementById('signup-password').value;
  const confirm = document.getElementById('signup-confirm').value;
  const err = document.getElementById('signup-error');
  if (pw !== confirm) { err.textContent = 'Passwords do not match.'; err.classList.add('show'); return; }
  err.classList.remove('show');
  try {
    const res = await fetch('/auth/signup', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: document.getElementById('signup-name').value, email: document.getElementById('signup-email').value, password: pw })
    });
    const data = await res.json();
    if (!res.ok) { err.textContent = data.error || 'Signup failed.'; err.classList.add('show'); return; }
    err.style.color = '#4ade80'; err.textContent = data.message; err.classList.add('show');
    document.getElementById('form-signup').querySelector('.login-btn').disabled = true;
  } catch (e) {
    err.textContent = 'Could not reach server.'; err.classList.add('show');
  }
}

async function init() {
  try {
    const res = await fetch('/api/me');
    if (!res.ok) return; // stay on login overlay
    const me = await res.json();
    document.getElementById('login-overlay').classList.add('hidden');
    setUser(me.name);
    render(me.role === 'admin', me.access);
  } catch (e) {
    // stay on login overlay — server not reachable
  }
}

init();
