# PawFresh Chat Automation — Python backend
https://pawfresh-4sgo25ru1-ananya-1210.vercel.app/


A real Python backend for the PawFresh customer-service bot: a rule-based
engine (`bot_engine.py`) plus two ways to talk to it — a browser chat demo
and a webhook shaped exactly like Meta's WhatsApp Cloud API, ready to
connect to a real WhatsApp number.

No paid services required to run or demo this.

## Files

| File | Purpose |
|---|---|
| `bot_engine.py` | The bot's logic: intent matching and replies. No web framework, no network calls — pure Python, easy to read and extend. |
| `cli_demo.py` | Chat with the bot in a terminal. Good for quickly testing new rules. |
| `app.py` | Flask app: a browser chat UI at `/`, plus a `/webhook` route for real WhatsApp messages. |
| `templates/index.html` | The browser chat UI used by `app.py`. |
| `requirements.txt` | The two dependencies (Flask, requests). |

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Try it in the terminal (no server at all)

```bash
python cli_demo.py
```

Type things like `hi`, `price of puppy food`, `track order`, `allergies`,
`bye`. This is the fastest way to test changes to `bot_engine.py`.

## Try it in the browser

```bash
python app.py
```

Open `http://localhost:5000`. This runs the same `bot_engine.py`, over a
real HTTP request/response cycle, with session state kept per browser —
close and reopen the tab and it starts a fresh conversation.

## Connecting it to a real WhatsApp number (free tier)

Meta's WhatsApp Business Cloud API has a free tier that's enough for
testing and a low-to-moderate volume of real conversations. Rough steps:

1. Create a Meta developer account and app at
   [developers.facebook.com](https://developers.facebook.com), and add the
   **WhatsApp** product to it.
2. Meta gives you a test phone number and a temporary access token for
   free — enough to send/receive messages from your own WhatsApp during
   development.
3. Set three environment variables before running `app.py`:
   ```bash
   export WHATSAPP_TOKEN="your-access-token"
   export PHONE_NUMBER_ID="your-phone-number-id"
   export VERIFY_TOKEN="pick-any-string-you-like"
   ```
4. Run `app.py`, then expose it to the internet so Meta can reach it —
   for local testing, a tunnel tool like `ngrok` works:
   ```bash
   ngrok http 5000
   ```
5. In the Meta app dashboard, set the webhook URL to
   `https://<your-ngrok-domain>/webhook` and the verify token to the same
   `VERIFY_TOKEN` you set above. Meta will call the endpoint once to
   confirm it (`app.py` already handles that handshake).
6. Message the test WhatsApp number from your phone — replies come back
   through `_send_whatsapp_message()` in `app.py`, using the same
   `bot_engine.py` logic as the browser demo.

Without those three environment variables set, `/webhook` still runs —
it just prints what it *would have* sent instead of calling the WhatsApp
API, so nothing breaks if you deploy it before getting credentials.

**Instagram DMs** use a separate but very similar Meta API (Instagram
Messaging API), also free at this scale, with the same webhook shape —
extending `app.py` to handle both channels from one codebase is a small
follow-up, not a rebuild.

## Extending the bot

All of the actual conversation logic lives in `bot_engine.py`, in the
`_PATTERNS` list and the `_handle()` method. To add a new topic:

1. Add a `(name, regex)` pair to `_PATTERNS`.
2. Add an `if intent == "name":` branch in `_handle()` that returns a
   `BotReply(...)`.

Order matters in `_PATTERNS` — more specific patterns should come before
more general ones, since the first match wins.

## Upgrading to AI-generated replies later

This version is entirely rule-based, which is what keeps it free to run.
The one part of the system with a genuine running cost is swapping the
pattern-matching in `_match_intent()` for a language model call, which
lets the bot understand phrasing it hasn't been explicitly written for.
That's a deliberate later step, not something this version needs.


