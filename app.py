"""
app.py

Two ways to talk to the same bot_engine.PawFreshBot:

1. A tiny browser chat UI at "/" — for demoing without any WhatsApp/Instagram
   setup at all. Good for a client pitch on a laptop.

2. A "/webhook" route shaped exactly like Meta's WhatsApp Cloud API webhook.
   Point a real WhatsApp Business number at this route (see README.md) and
   it will reply for real, using the free tier of Meta's API — no code
   changes needed, just environment variables.

Run:
    python app.py
Then open http://localhost:5000
"""

import os
import uuid

import requests
from flask import Flask, jsonify, render_template, request, session

from bot_engine import PawFreshBot

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-secret-change-me")

bot = PawFreshBot()

# In-memory session store keyed by a per-sender id: { sender_id: {..state..} }.
# Fine for a demo; swap for Redis/a database before real production traffic.
_sessions = {}

# --- WhatsApp Cloud API credentials (all optional — only needed to send
# real WhatsApp messages; the browser demo works with none of these set). ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "pawfresh-verify-token")


# ---------------------------------------------------------------------------
# Browser demo
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "client_id" not in session:
        session["client_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    client_id = session.get("client_id", "anonymous")

    user_session = _sessions.setdefault(client_id, {})
    reply = bot.get_reply(message, user_session)

    return jsonify(reply=reply.text, quick_replies=reply.quick_replies)


# ---------------------------------------------------------------------------
# Real WhatsApp Cloud API webhook
# (see README.md for how to get a free access token and connect this)
# ---------------------------------------------------------------------------

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta calls this once, with these query params, to confirm you own
    the endpoint before it will send you any messages."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Handles incoming WhatsApp messages in Meta's Cloud API payload shape."""
    payload = request.get_json(force=True) or {}

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]["value"]
        message = change["messages"][0]
        sender_id = message["from"]
        text = message.get("text", {}).get("body", "")
    except (KeyError, IndexError):
        # Not a user message (e.g. a delivery-status update) — ignore it.
        return jsonify(status="ignored"), 200

    user_session = _sessions.setdefault(sender_id, {})
    reply = bot.get_reply(text, user_session)

    if WHATSAPP_TOKEN and PHONE_NUMBER_ID:
        _send_whatsapp_message(sender_id, reply.text)
    else:
        # Demo mode: no credentials configured yet, so just log the reply
        # instead of sending it. Everything else about this endpoint is
        # real and ready to go once WHATSAPP_TOKEN and PHONE_NUMBER_ID
        # are set (see README.md).
        print(f"[DEMO MODE — would reply to {sender_id}]: {reply.text}")

    return jsonify(status="ok"), 200


def _send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    response = requests.post(url, headers=headers, json=body, timeout=10)
    if not response.ok:
        print(f"[WhatsApp send failed] {response.status_code}: {response.text}")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
