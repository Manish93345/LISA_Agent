"""
LISA — Voice Mode
==================
Usage: python voice_main.py

Bol ke band karo: "bye lisa" / "alvida" / "band karo"
"""

from core.agent      import LisaAgent
from voice.stt       import listen_once
from voice.tts       import speak
from config.settings import AGENT_NAME, USER_NAME


def main():
    print("\n" + "="*55)
    print(f"   {AGENT_NAME.upper()} — Voice Mode")
    print("="*55)
    print("   Bolo — main sun rhi hoon!")
    print("   Band karne ke liye bolo: 'bye lisa'")
    print("="*55 + "\n")

    agent = LisaAgent()

    greeting = f"Haan {USER_NAME}, main sun rhi hoon! Bolo na."
    print(f"{AGENT_NAME}: {greeting}\n")
    speak(greeting)

    while True:
        try:
            user_text = listen_once(max_seconds=30)

            if not user_text:
                continue

            if user_text == "quit":
                break

            # Exit commands
            exit_words = ["bye lisa", "alvida", "band karo", "quit", "exit"]
            if any(x in user_text.lower() for x in exit_words):
                farewell = "Theek hai, alvida! Take care."
                print(f"\n{AGENT_NAME}: {farewell}\n")
                speak(farewell)
                break

            print(f"{USER_NAME}: {user_text}")

            reply = agent.chat(user_text)
            print(f"{AGENT_NAME}: {reply}\n")
            speak(reply)

        except KeyboardInterrupt:
            print(f"\n\n  Alvida!\n")
            break


if __name__ == "__main__":
    main()