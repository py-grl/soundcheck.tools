
    // index must match each user's access[] array. "Portals" (3) gates all
    // three portal tools on the homepage — Package Tracking, Tracking Number
    // Search, and Maintenance Portal — as one permission, one checkbox here.
    const apps = ['Noke','Dock Scheduler','Checkout','Portals','Parking','Noke2Excel', 'Sharepoint', 'Community', 'Admin'];
    let users = [];

    const checkSVG = `<svg viewBox="0 0 14 14" width="14" height="14" fill="none" stroke="#1a1a00" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,7 6,11 12,3"/></svg>`;

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2000);
    }

    const trashSVG = `<svg viewBox="0 0 14 14" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,3 13,3"/><path d="M5,3V2h4v1"/><path d="M2,3l1,9h8l1-9"/><line x1="5.5" y1="6" x2="5.5" y2="10"/><line x1="8.5" y1="6" x2="8.5" y2="10"/></svg>`;

    const clockSVG = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/></svg>`;

    function histEscape(s) {
      return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }
    function histActionClass(a) {
      return ['create','edit','delete','approve','permissions'].includes(a) ? a : 'default';
    }
    function histFmtTime(ts) {
      if (!ts) return '';
      const s = /[zZ]$|[+\-]\d\d:?\d\d$/.test(ts) ? ts : ts + 'Z';
      const d = new Date(s);
      return isNaN(d) ? ts : d.toLocaleString('en-US',
        { month:'short', day:'numeric', year:'numeric', hour:'numeric', minute:'2-digit' });
    }

    async function openHistory(userId, userName) {
      document.getElementById('hist-title').textContent = userName + ' — History';
      const content = document.getElementById('hist-content');
      content.innerHTML = '<div class="h-empty">Loading…</div>';
      document.getElementById('hist-modal').classList.add('show');
      try {
        const res = await fetch(`/api/history/user/${userId}`);
        if (!res.ok) { content.innerHTML = '<div class="h-empty">Could not load history.</div>'; return; }
        const logs = await res.json();
        if (!logs.length) {
          content.innerHTML = '<div class="h-empty">No history recorded for this user yet.</div>';
          return;
        }
        content.innerHTML = logs.map(l => `
          <div class="h-item">
            <span class="h-badge ${histActionClass(l.action)}">${histEscape(l.action)}</span>
            <div>
              <div class="h-detail">${l.detail ? histEscape(l.detail) : histEscape(l.action)}</div>
              <div class="h-meta">${histFmtTime(l.timestamp)}${l.user ? ' · ' + histEscape(l.user) : ''}${l.source ? ' · ' + histEscape(l.source) : ''}</div>
            </div>
          </div>`).join('');
      } catch (e) {
        content.innerHTML = '<div class="h-empty">Cannot reach the server.</div>';
      }
    }

    function closeHistory() {
      document.getElementById('hist-modal').classList.remove('show');
    }

    document.getElementById('hist-modal').addEventListener('click', function(e) {
      if (e.target === this) closeHistory();
    });

    async function approveUser(user, statusTd) {
      const res = await fetch(`/api/users/${user.id}/approve`, { method: 'PATCH' });
      if (res.ok) {
        user.approved = true;
        statusTd.innerHTML = `<span class="approved-badge">Approved</span>`;
        showToast(`${user.name} approved — they can now log in`);
      }
    }

    function renderTable() {
      const tbody = document.getElementById('tbody');
      tbody.innerHTML = '';

      users.forEach(user => {
        const tr = document.createElement('tr');

        const nameTd = document.createElement('td');
        nameTd.className = 'name-cell';
        nameTd.innerHTML = `<div class="user-info">
          <div class="avatar" style="background:${user.color};color:${user.text};">${user.initials}</div>
          <div>
            <div class="user-name">${user.name}</div>
            <div class="user-role">${user.role}</div>
          </div>
        </div>`;
        tr.appendChild(nameTd);

        const statusTd = document.createElement('td');
        if (user.approved) {
          statusTd.innerHTML = `<span class="approved-badge">Approved</span>`;
        } else {
          const approveBtn = document.createElement('button');
          approveBtn.className = 'approve-btn';
          approveBtn.textContent = 'Pending — Approve';
          approveBtn.onclick = () => approveUser(user, statusTd);
          statusTd.appendChild(approveBtn);
        }
        tr.appendChild(statusTd);

        apps.forEach((app, ai) => {
          const td = document.createElement('td');
          const btn = document.createElement('div');
          btn.className = 'toggle' + (user.access[ai] ? ' on' : '');
          btn.innerHTML = user.access[ai] ? checkSVG : '';
          btn.onclick = () => {
            user.access[ai] = !user.access[ai];
            btn.classList.toggle('on', user.access[ai]);
            btn.innerHTML = user.access[ai] ? checkSVG : '';
            tr.classList.add('dirty');
            pushBtn.classList.add('dirty');
          };
          td.appendChild(btn);
          tr.appendChild(td);
        });

        const pushTd = document.createElement('td');
        const pushBtn = document.createElement('button');
        pushBtn.className = 'push-btn';
        pushBtn.textContent = 'Push';
        pushBtn.onclick = async () => {
          const res = await fetch(`/api/users/${user.id}/permissions`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ access: user.access })
          });
          if (res.ok) {
            tr.classList.remove('dirty');
            pushBtn.classList.remove('dirty');
            showToast(`${user.name}'s permissions saved`);
          }
        };
        pushTd.appendChild(pushBtn);
        tr.appendChild(pushTd);

        const removeTd = document.createElement('td');
        const rowActions = document.createElement('div');
        rowActions.className = 'row-actions';

        const histBtn = document.createElement('button');
        histBtn.className = 'hist-btn';
        histBtn.innerHTML = clockSVG;
        histBtn.title = `History for ${user.name}`;
        histBtn.onclick = () => openHistory(user.id, user.name);
        rowActions.appendChild(histBtn);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.innerHTML = trashSVG;
        removeBtn.title = `Remove ${user.name}`;
        removeBtn.onclick = async () => {
          if (!confirm(`Remove ${user.name}? They'll need to sign up again.`)) return;
          const res = await fetch(`/api/users/${user.id}`, { method: 'DELETE' });
          if (res.ok) {
            tr.remove();
            showToast(`${user.name} removed`);
          }
        };
        rowActions.appendChild(removeBtn);

        removeTd.appendChild(rowActions);
        tr.appendChild(removeTd);
        tbody.appendChild(tr);
      });
    }

    async function init() {
      try {
        const res = await fetch('/api/users');
        if (res.status === 401) { window.location.href = '/login'; return; }
        if (!res.ok) { showError(`Server error ${res.status} — try refreshing.`); return; }
        users = await res.json();
        renderTable();
      } catch (e) {
        showError('Cannot reach the server. Make sure the Flask app is running.');
      }
    }

    function showError(msg) {
      document.getElementById('tbody').innerHTML = `<tr><td colspan="10" style="padding:2rem;color:#ef4444;font-size:13px;">${msg}</td></tr>`;
    }

    init();
