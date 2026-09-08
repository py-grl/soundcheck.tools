from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

# Local preview only — the real backend (with real login) is
# soundcheck.tools/ADMIN/app.py. This stub just fakes a logged-in
# user so the login overlay doesn't block viewing the static page.
FAKE_USER = {"name": "Local Preview", "role": "admin", "access": [True] * 10}


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/me")
def api_me():
    return jsonify(FAKE_USER)


if __name__ == "__main__":
    app.run(debug=True)
