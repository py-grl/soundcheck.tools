from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json, os, uuid, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Logger'))
from logger import log_action, get_record_logs
from identity import SHARED_SECRET, current_user_name

app = Flask(__name__, static_folder='.')
app.secret_key = SHARED_SECRET
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

COLORS = [
    ('#E6F1FB', '#185FA5'), ('#EAF3DE', '#3B6D11'), ('#FAEEDA', '#854F0B'),
    ('#FCE7F3', '#9D174D'), ('#EDE9FE', '#5B21B6'), ('#D1FAE5', '#065F46'),
    ('#FEE2E2', '#991B1B'), ('#FEF3C7', '#92400E'),
]


def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        data = load_users()
        user = next((u for u in data['users'] if u['id'] == session['user_id']), None)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated


# ── static pages ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return send_from_directory('.', 'LOGIN.SIGNUP.html')
    return send_from_directory('..', 'index.html')

@app.route('/admin')
@require_admin
def admin_page():
    return send_from_directory('.', 'ADMIN.html')

@app.route('/api/check-auth')
def check_auth():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return '', 200


@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_users()
    user = next((u for u in data['users'] if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'name': user['name'], 'role': user['role'], 'access': user.get('access', [])})


# ── auth ──────────────────────────────────────────────────────────────────────

@app.route('/auth/login', methods=['POST'])
def auth_login():
    body = request.get_json()
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')

    data = load_users()
    user = next((u for u in data['users'] if u['email'].lower() == email), None)

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Incorrect email or password.'}), 401

    if not user.get('approved'):
        return jsonify({'error': 'Your account is pending admin approval.'}), 403

    session['user_id'] = user['id']
    session['role'] = user.get('role', 'employee')
    log_action('login', user=user['name'], source='ADMIN', detail=f"{user['email']} logged in")

    return jsonify({'role': user.get('role', 'employee'), 'name': user['name']})


@app.route('/auth/signup', methods=['POST'])
def auth_signup():
    body = request.get_json()
    name = body.get('name', '').strip()
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required.'}), 400

    data = load_users()
    if any(u['email'].lower() == email for u in data['users']):
        return jsonify({'error': 'An account with that email already exists.'}), 409

    initials = ''.join(p[0].upper() for p in name.split()[:2])
    color_pair = COLORS[len(data['users']) % len(COLORS)]

    new_user = {
        'id': str(uuid.uuid4()),
        'name': name,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': 'employee',
        'color': color_pair[0],
        'text': color_pair[1],
        'initials': initials,
        'access': [False, False, False, False, False, False, False],
        'approved': False
    }

    data['users'].append(new_user)
    save_users(data)
    log_action('signup', user=name, source='ADMIN', detail=f'{email} signed up — pending approval')

    return jsonify({'message': 'Account created. Awaiting admin approval.'})


@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    data = load_users()
    user = next((u for u in data['users'] if u['id'] == session.get('user_id')), None)
    log_action('logout', user=user['name'] if user else None, source='ADMIN')
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/auth/forgot', methods=['POST'])
def auth_forgot():
    # Wire up an email provider (e.g. SendGrid) here when ready
    return jsonify({'message': 'If that email exists, a reset link has been sent.'})


# ── users api ─────────────────────────────────────────────────────────────────

@app.route('/api/users', methods=['GET'])
@require_admin
def get_users():
    data = load_users()
    safe = [{k: v for k, v in u.items() if k != 'password_hash'} for u in data['users']]
    return jsonify(safe)


@app.route('/api/users/<user_id>/permissions', methods=['PATCH'])
@require_admin
def update_permissions(user_id):
    body = request.get_json()
    access = body.get('access')

    if not isinstance(access, list) or len(access) != 7:
        return jsonify({'error': 'Invalid access array — must be 7 booleans'}), 400

    data = load_users()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['access'] = access
    user['role'] = 'admin' if access[6] else 'employee'
    save_users(data)
    log_action('permissions', user=current_user_name(session), source='ADMIN',
               target_type='user', target_id=user_id,
               detail=f"Updated permissions for {user['name']}")
    return jsonify({'message': 'Permissions updated'})


@app.route('/api/users/<user_id>/approve', methods=['PATCH'])
@require_admin
def approve_user(user_id):
    data = load_users()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['approved'] = True
    save_users(data)
    log_action('approve', user=current_user_name(session), source='ADMIN',
               target_type='user', target_id=user_id,
               detail=f"Approved account for {user['name']}")
    return jsonify({'message': 'User approved'})


@app.route('/api/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    data = load_users()
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data['users'] = [u for u in data['users'] if u['id'] != user_id]
    save_users(data)
    log_action('delete', user=current_user_name(session), source='ADMIN',
               target_type='user', target_id=user_id,
               detail=f"Removed account for {user['name']}")
    return jsonify({'message': 'User removed'})


@app.route('/api/history/<target_type>/<target_id>', methods=['GET'])
@require_admin
def get_history(target_type, target_id):
    return jsonify(get_record_logs(target_type, target_id))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
