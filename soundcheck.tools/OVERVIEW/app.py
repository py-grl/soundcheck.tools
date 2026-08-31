import os
import sys
from functools import wraps

from flask import Flask, jsonify, send_from_directory, session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Logger'))
from identity import SHARED_SECRET, current_user

# static_folder=None: see ADMIN/app.py for why — avoids Flask auto-serving
# every file in this directory with no auth check.
app = Flask(__name__, static_folder=None)
app.secret_key = SHARED_SECRET


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user(session)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated


@app.route('/overview')
@require_admin
def overview_page():
    return send_from_directory('.', 'OVERVIEW.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)
