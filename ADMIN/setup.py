from werkzeug.security import generate_password_hash
import json, uuid

pw = input("Set your password: ")
data = {
    "users": [
        {
            "id": str(uuid.uuid4()),
            "name": "Jackie Herrman",
            "email": "jacki3herrman@gmail.com",
            "password_hash": generate_password_hash(pw),
            "role": "admin",
            "color": "#fff200",
            "text": "#5a4d00",
            "initials": "JH",
            "access": [True, True, True, True, True, True, True],
            "approved": True
        }
    ]
}

with open("/var/www/html/ADMIN/users.json", "w") as f:
    json.dump(data, f, indent=2)

print("Done! Login with jacki3herrman@gmail.com and your new password.")
