import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
COMPANY_NAME = os.getenv("COMPANY_NAME", "NOKE Smart Entry")

# Opt-out footer required by TCPA
SMS_FOOTER = "\n\nReply STOP to unsubscribe."


def send_sms(to_phone, message, contact_name=""):
    """Send an SMS via Twilio."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        full_message = message + SMS_FOOTER

        msg = client.messages.create(
            body=full_message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )

        return {
            "success": True,
            "contact": contact_name,
            "phone": to_phone,
            "sid": msg.sid
        }

    except Exception as e:
        return {
            "success": False,
            "contact": contact_name,
            "phone": to_phone,
            "error": str(e)
        }


