from flask import Flask, render_template, request, jsonify, session
from contacts import load_contacts, get_group
from messenger import send_sms
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'Logger'))
from logger import log_action
from identity import SHARED_SECRET, current_user_name

app = Flask(__name__)
app.secret_key = SHARED_SECRET

@app.route("/")
def index():
    contacts = load_contacts()
    camps = sorted(set(c["unit_name"] for c in contacts if c["unit_name"]))
    return render_template("index.html", camps=camps)

@app.route("/api/contacts")
def api_contacts():
    group = request.args.get("group", "all")
    camp = request.args.get("camp", None)
    contacts = load_contacts()
    filtered = get_group(contacts, group, camp)
    return jsonify(filtered)

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json
    message = data.get("message", "").strip()
    recipients = data.get("recipients", [])
    channels = data.get("channels", ["sms"])

    if not message:
        return jsonify({"error": "Message is required"}), 400
    if not recipients:
        return jsonify({"error": "No recipients selected"}), 400

    results = {"sms": [],}

    for contact in recipients:
        if "sms" in channels and contact.get("phone"):
            result = send_sms(contact["phone"], message, contact["name"])
            results["sms"].append(result)

    success_sms = sum(1 for r in results["sms"] if r["success"])

    log_action('send', user=current_user_name(session), source='NOKEtheMESSENGER',
               detail=f'SMS sent to {success_sms}/{len(recipients)} recipients')

    return jsonify({
        "success": True,
        "sms_sent": success_sms,
        "details": results
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
