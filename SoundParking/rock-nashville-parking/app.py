from flask import Flask, request, jsonify, send_from_directory, session, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Logger'))
from logger import log_action, get_record_logs
from identity import SHARED_SECRET, current_user_name, current_user

app = Flask(__name__, static_folder='public')
app.secret_key = SHARED_SECRET
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

DB_PATH = os.path.join(os.path.dirname(__file__), 'parking.db')


# ── Auth gate ───────────────────────────────────────────────────────────────────
# Parking has no login of its own — ADMIN owns login and signs the session cookie
# with the shared SECRET_KEY. Because we set the same secret above, we can read that
# session and require the visitor be a logged-in, approved user who's been granted
# Parking before they touch ANY route.

# "Parking" is access index 4 in ADMIN's permissions array (see index.html).
PARKING_ACCESS_INDEX = 4

# Where to send visitors who aren't logged in. In production every tool shares the
# soundcheck.tools domain, so the site root serves ADMIN's login page. Override with
# LOGIN_URL when running standalone (e.g. http://localhost:5000/ in dev).
LOGIN_URL = os.environ.get('LOGIN_URL', '/')


@app.before_request
def require_parking_access():
    # Let static assets (CSS/JS) through; everything else needs a valid session.
    if request.endpoint == 'static':
        return None
    user = current_user(session)
    if not user or not user.get('approved'):
        return redirect(LOGIN_URL)
    access = user.get('access') or []
    if len(access) <= PARKING_ACCESS_INDEX or not access[PARKING_ACCESS_INDEX]:
        # Logged in but not granted Parking — send back to the hub.
        return redirect(LOGIN_URL)
    return None


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            company   TEXT NOT NULL,
            spots     INTEGER NOT NULL,
            start     TEXT NOT NULL,
            end       TEXT,
            contact   TEXT,
            lease     TEXT,
            notes     TEXT,
            created   TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    return conn


def row_to_dict(row):
    return dict(row)


# ── Static ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    conn = get_db()
    rows = conn.execute('SELECT * FROM reservations ORDER BY created DESC').fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    body = request.get_json()
    company = (body.get('company') or '').strip()
    spots   = body.get('spots')
    start   = (body.get('start') or '').strip()

    if not company or not spots or not start:
        return jsonify({'error': 'Company, spots, and start date are required.'}), 400

    conn = get_db()
    cur = conn.execute(
        'INSERT INTO reservations (company, spots, start, end, contact, lease, notes) VALUES (?,?,?,?,?,?,?)',
        (company, int(spots), start,
         body.get('end') or None,
         (body.get('contact') or '').strip() or None,
         body.get('lease') or None,
         (body.get('notes') or '').strip() or None)
    )
    conn.commit()
    new_row = row_to_dict(conn.execute('SELECT * FROM reservations WHERE id = ?', (cur.lastrowid,)).fetchone())
    conn.close()

    log_action('create', user=current_user_name(session), source='SoundParking',
               target_type='reservation', target_id=new_row['id'],
               detail=f"{company} — {spots} spot(s) starting {start}")
    return jsonify(new_row)


@app.route('/api/reservations/<int:res_id>', methods=['PUT'])
def update_reservation(res_id):
    body = request.get_json()
    company = (body.get('company') or '').strip()
    spots   = body.get('spots')
    start   = (body.get('start') or '').strip()

    if not company or not spots or not start:
        return jsonify({'error': 'Company, spots, and start date are required.'}), 400

    conn = get_db()
    conn.execute(
        'UPDATE reservations SET company=?, spots=?, start=?, end=?, contact=?, lease=?, notes=? WHERE id=?',
        (company, int(spots), start,
         body.get('end') or None,
         (body.get('contact') or '').strip() or None,
         body.get('lease') or None,
         (body.get('notes') or '').strip() or None,
         res_id)
    )
    conn.commit()
    updated = conn.execute('SELECT * FROM reservations WHERE id = ?', (res_id,)).fetchone()
    conn.close()

    if not updated:
        return jsonify({'error': 'Not found'}), 404

    log_action('edit', user=current_user_name(session), source='SoundParking',
               target_type='reservation', target_id=res_id,
               detail=f"{company} — {spots} spot(s) starting {start}")
    return jsonify(row_to_dict(updated))


@app.route('/api/history/<target_type>/<int:target_id>', methods=['GET'])
def get_history(target_type, target_id):
    return jsonify(get_record_logs(target_type, target_id))


@app.route('/api/reservations/<int:res_id>', methods=['DELETE'])
def delete_reservation(res_id):
    conn = get_db()
    conn.execute('DELETE FROM reservations WHERE id = ?', (res_id,))
    conn.commit()
    conn.close()

    log_action('delete', user=current_user_name(session), source='SoundParking',
               target_type='reservation', target_id=res_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, port=5003)
