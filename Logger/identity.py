"""Shared identity helper.

Lets every Soundcheck app figure out *who* is acting, so the logger can record
who did what (not just what/when/where). ADMIN owns login and the user list;
this module reads ADMIN's signed Flask session cookie (using the same
SECRET_KEY) and resolves the session's user id against ADMIN/users.json.

Flask apps: set ``app.secret_key = SHARED_SECRET`` so they can verify ADMIN's
session, then pass ``user=current_user_name(session)`` to ``log_action``.
"""
import os
import json

# The exact key ADMIN signs its session cookie with. Every Flask app must use
# this same value so they can all read ADMIN's login session. In production,
# set SECRET_KEY to one identical value across every service.
SHARED_SECRET = os.environ.get(
    'SECRET_KEY',
    'bca5887b84e6d7080497c4d733b742b0911027f0242ebd71bcbd90095be0d019'
)

# users.json lives in ADMIN; this module sits in Logger/ (a sibling folder).
USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'ADMIN', 'users.json')


def _load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f).get('users', [])
    except (OSError, ValueError):
        return []


def user_name_for_id(user_id):
    """Resolve a user id (as stored in the session) to a display name, or None."""
    if not user_id:
        return None
    for u in _load_users():
        if u.get('id') == user_id:
            return u.get('name')
    return None


def current_user_name(session):
    """Display name of the logged-in user for a Flask ``session``, or None.

    Returns None when no one is logged in (e.g. the session cookie isn't
    present), so callers can log ``user=None`` without extra guarding.
    """
    return user_name_for_id(session.get('user_id'))


def current_user(session):
    """Full user record for the logged-in Flask ``session``, or None.

    Lets apps gate access on ``approved`` / ``access`` (not just learn the name)
    for the person behind ADMIN's shared session cookie. Flask only populates
    ``session['user_id']`` when the cookie's signature checks out against the
    shared SECRET_KEY, so a present user id is already an authenticated one.
    Returns None when nobody is logged in.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    for u in _load_users():
        if u.get('id') == user_id:
            return u
    return None
