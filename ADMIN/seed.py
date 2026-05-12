"""
Run once: python seed.py
Creates users.json with the 4 base users. You'll be prompted to set Jackie's password.
"""
from werkzeug.security import generate_password_hash
import json, uuid

password = input("Set Jackie's password: ").strip()

users = [
    {
        'id': str(uuid.uuid4()),
        'name': 'Jackie',
        'email': 'jherrman@soundchecknashville.com',
        'password_hash': generate_password_hash(password),
        'role': 'admin',
        'color': '#fff200',
        'text': '#5a4d00',
        'initials': 'JA',
        'access': [True, True, True, True, True, True, True],
        'approved': True
    },
    {
        'id': str(uuid.uuid4()),
        'name': 'Ariana',
        'email': 'ariana@clairglobal.com',
        'password_hash': generate_password_hash('changeme'),
        'role': 'employee',
        'color': '#E6F1FB',
        'text': '#185FA5',
        'initials': 'AR',
        'access': [False, False, False, False, False, False, False],
        'approved': True
    },
    {
        'id': str(uuid.uuid4()),
        'name': 'Cozy',
        'email': 'cozy@clairglobal.com',
        'password_hash': generate_password_hash('changeme'),
        'role': 'employee',
        'color': '#EAF3DE',
        'text': '#3B6D11',
        'initials': 'CO',
        'access': [False, False, False, False, False, False, False],
        'approved': True
    },
    {
        'id': str(uuid.uuid4()),
        'name': 'Ryan',
        'email': 'ryan@clairglobal.com',
        'password_hash': generate_password_hash('changeme'),
        'role': 'employee',
        'color': '#FAEEDA',
        'text': '#854F0B',
        'initials': 'RY',
        'access': [False, False, False, False, False, False, False],
        'approved': True
    },
]

with open('users.json', 'w') as f:
    json.dump({'users': users}, f, indent=2)

print("✓ users.json created. Other users have default password: changeme")
print("  Have them log in and change it, or update their emails above and re-run.")
