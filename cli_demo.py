"""
cli_demo.py

Talk to the PawFresh bot straight from the terminal — useful for testing
bot_engine.py in isolation, with no Flask, no browser, no network at all.

Run:
    python cli_demo.py
"""

from bot_engine import PawFreshBot


def main():
    bot = PawFreshBot()
    session = {}

    print("PawFresh Pet Nutrition — bot demo (type 'quit' to exit)\n")
    greeting = bot.get_reply("hi", session)
    print(f"Bot: {greeting.text}")
    if greeting.quick_replies:
        print(f"     [Quick replies: {', '.join(greeting.quick_replies)}]")

    while True:
        try:
            user_msg = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Take care!")
            break

        if user_msg.lower() in ("quit", "exit"):
            print("Bot: Take care!")
            break

        reply = bot.get_reply(user_msg, session)
        print(f"Bot: {reply.text}")
        if reply.quick_replies:
            print(f"     [Quick replies: {', '.join(reply.quick_replies)}]")


if __name__ == "__main__":
    main()
