"""
bot_engine.py

The reusable "brain" of the PawFresh customer-service bot.

This module knows nothing about WhatsApp, Instagram, or the web — it just
takes a message plus a per-user session dict, and returns a reply plus a
list of quick-reply suggestions. app.py (or cli_demo.py) wires this up to
an actual channel.

No paid APIs, no external ML model — pattern matching on plain text.
That keeps it free to run, at the cost of only handling questions it has
been written for. See README.md for how to upgrade to an LLM later.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BotReply:
    text: str
    quick_replies: list = field(default_factory=list)


MENU = [
    "Product info",
    "Pricing",
    "Delivery",
    "Track order",
    "Ingredients & allergies",
    "Talk to a person",
]

CATALOG = {
    "puppy": {
        "label": "Puppy Formula",
        "blurb": "For pups 0-12 months. Real chicken, DHA for brain development, "
                 "calcium for healthy bone growth.",
        "price_1_5kg": 649,
        "price_3kg": 1199,
    },
    "adult": {
        "label": "Adult Formula",
        "blurb": "Balanced daily nutrition built around chicken and rice.",
        "price_1_5kg": 599,
        "price_3kg": 1099,
    },
    "senior": {
        "label": "Senior Formula",
        "blurb": "For dogs 7+ years. Lower calorie, added glucosamine for joint "
                 "support, easy-to-digest protein.",
        "price_1_5kg": 699,
        "price_3kg": 1299,
    },
    "grain_free": {
        "label": "Grain-Free",
        "blurb": "For dogs with wheat or grain sensitivities.",
        "price_1_5kg": 799,
        "price_3kg": 1449,
    },
}

# Ordered list of (name, regex, handler_name). Order matters: first match wins,
# so more specific patterns should sit above general ones.
_PATTERNS = [
    ("greeting", r"\b(hi|hello|hey|namaste|good (morning|afternoon|evening))\b"),
    ("puppy", r"\bpuppy\b"),
    ("senior", r"\bsenior\b|\bold dog\b"),
    ("adult", r"\badult\b"),
    ("grain_free", r"\bgrain[- ]?free\b"),
    ("ingredients", r"\bingredient|allerg|gluten|grain\b"),
    ("price", r"\bpric|cost|rate|how much\b"),
    ("delivery", r"\bdeliver|shipping|ship\b"),
    ("track_order", r"\btrack|order status|where is my order\b"),
    ("payment", r"\bpayment|cod|cash on delivery|upi|pay\b"),
    ("returns", r"\breturn|refund|exchange\b"),
    ("human", r"\bagent|human|representative|talk to (a )?person\b"),
    ("product_info", r"\bproduct|catalog|range|options|dog food\b"),
    ("thanks", r"\bthank(s| you)?|great|ok(ay)?\b"),
    ("bye", r"\bbye|goodbye\b"),
]
_COMPILED = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in _PATTERNS]


class PawFreshBot:
    """
    Stateless engine + per-user session state.

    Usage:
        bot = PawFreshBot()
        session = {}  # persist this per user_id between messages
        reply = bot.get_reply("hi", session)
    """

    def get_reply(self, message: str, session: dict) -> BotReply:
        message = (message or "").strip()

        # Multi-turn flow: bot previously asked for an order ID.
        if session.get("awaiting_order_id"):
            session["awaiting_order_id"] = False
            order_id = re.sub(r"\D", "", message) or "10482"
            return BotReply(
                f"Thanks! Order #{order_id} is packed and out for delivery — "
                f"expected by tomorrow, 6-8 PM.\n\nAnything else I can help with?",
                MENU,
            )

        intent = self._match_intent(message)
        return self._handle(intent, session)

    def _match_intent(self, message: str) -> Optional[str]:
        for name, pattern in _COMPILED:
            if pattern.search(message):
                return name
        return None

    def _handle(self, intent: Optional[str], session: dict) -> BotReply:
        if intent == "greeting":
            return BotReply(
                "Hi there! Welcome to PawFresh Pet Nutrition. I can help with "
                "product info, pricing, delivery, and order questions.\n\n"
                "What would you like to know?",
                MENU,
            )

        if intent in ("puppy", "senior", "adult", "grain_free"):
            item = CATALOG[intent]
            return BotReply(
                f"{item['label']}\n{item['blurb']}\n"
                f"Available in 1.5kg (Rs {item['price_1_5kg']}) and "
                f"3kg (Rs {item['price_3kg']}) packs.",
                ["Pricing", "Delivery"],
            )

        if intent == "product_info":
            lines = [f"- {v['label']}: {v['blurb']}" for v in CATALOG.values()]
            return BotReply(
                "Here's our range:\n" + "\n".join(lines) +
                "\n\nWant details or pricing on any of these?",
                ["Pricing", "Ingredients & allergies", "Puppy formula details"],
            )

        if intent == "price":
            lines = [
                f"- {v['label']}: Rs {v['price_1_5kg']} (1.5kg) / "
                f"Rs {v['price_3kg']} (3kg)"
                for v in CATALOG.values()
            ]
            return BotReply(
                "Here's our pricing:\n" + "\n".join(lines) +
                "\n\nAll orders above Rs 999 get free delivery!",
                ["Delivery", "Track order"],
            )

        if intent == "ingredients":
            return BotReply(
                "All PawFresh formulas use real meat as the first ingredient, "
                "with no artificial colors or preservatives. Our Grain-Free "
                "range suits dogs with wheat or grain sensitivities.\n\n"
                "Want the full ingredient sheet for a specific formula?",
                ["Puppy formula details", "Talk to a person"],
            )

        if intent == "delivery":
            return BotReply(
                "We deliver pan-India in 2-4 business days. Orders above "
                "Rs 999 ship free; below that, a flat Rs 49 delivery fee "
                "applies.\n\nWant to track an existing order instead?",
                ["Track order", "Pricing"],
            )

        if intent == "track_order":
            session["awaiting_order_id"] = True
            return BotReply("Sure — could you share your order ID? (e.g. #10482)")

        if intent == "payment":
            return BotReply(
                "We accept UPI, cards, net banking, and Cash on Delivery on "
                "most pin codes.",
                ["Delivery", "Pricing"],
            )

        if intent == "returns":
            return BotReply(
                "If a pack arrives damaged or your dog doesn't take to it, we "
                "offer a replacement or refund within 7 days of delivery — "
                "just share your order ID with support.",
                ["Talk to a person"],
            )

        if intent == "human":
            return BotReply(
                "Got it — connecting you to our support team now. Someone "
                "will reply here shortly. Anything quick I can help with "
                "meanwhile?",
                MENU,
            )

        if intent == "thanks":
            return BotReply("You're welcome! Happy to help anytime.")

        if intent == "bye":
            return BotReply("Take care, and give your pup a treat from us!")

        return BotReply(
            "I didn't quite catch that — here's what I can help with:",
            MENU,
        )
