# NOKE Messenger

A web app to send SMS and email messages to your contacts from your Excel sheet via Twilio.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your credentials
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- `TWILIO_ACCOUNT_SID` — from https://console.twilio.com
- `TWILIO_AUTH_TOKEN` — from https://console.twilio.com
- `TWILIO_PHONE_NUMBER` — your Twilio number (e.g. +16151234567)
- `EXCEL_PATH` — path to your contacts Excel file

### 3. Prepare your Excel file
Make sure your Excel sheet has these columns:
- `unit_id`
- `unit_name`
- `rental_state`
- `first_name`
- `last_name`
- `email`
- `phone`
- `shared_users` (names, comma separated)
- `shared_phones` (phones, comma separated)
- `sms_opt_out` (TRUE/FALSE — add this column, default FALSE for everyone)

### 4. Run the app
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

## Features
- Send to All Contacts, Primary Only, or Secondary Only
- Filter by Artist Camp
- SMS via Twilio + Email via SendGrid
- Auto-appends STOP opt-out footer (TCPA compliance)
- Character counter with SMS segment tracking
- Select/deselect individual recipients

## Compliance Notes
- All messages automatically include "Reply STOP to unsubscribe"
- Add `sms_opt_out = TRUE` in your sheet to exclude anyone who has opted out
- Keep records of consent (booking agreements, signed forms)
