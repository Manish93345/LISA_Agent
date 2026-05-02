"""
LISA — Main Entry Point
========================
Yahan se run karo:
    cd D:\\Study\\LISA_Agent
    python main.py

Commands:
    /mode         → current mode dekho
    /personal     → personal mode mein switch karo
    /professional → professional mode mein switch karo
    /remember category key value → manually kuch yaad karao
                   example: /remember academic cgpa 9.24
    /memories     → saari yaad ki hui cheezein dekho
    /reset        → conversation reset karo (memory rehti hai)
    /quit         → band karo
"""

from core.agent       import LisaAgent
from memory.long_term import list_all
from config.settings  import AGENT_NAME, USER_NAME

def print_banner():
    print("\n" + "="*55)
    print(f"   {AGENT_NAME.upper()} — Personal AI Agent")
    print("="*55)
    print(f"   Namaste {USER_NAME}! Main {AGENT_NAME} hoon.")
    print(f"   Type /quit to exit | /mode to check mode")
    print("="*55 + "\n")


def handle_command(cmd: str, agent: LisaAgent) -> bool:
    """
    Special commands handle karo.
    Returns True agar command tha, False agar normal message tha.
    """
    parts = cmd.strip().split(maxsplit=3)
    c     = parts[0].lower()

    if c == "/quit":
        print(f"\n  {AGENT_NAME}: Theek hai, alvida! Take care. 👋\n")
        return "EXIT"

    elif c == "/mode":
        print(f"  [Current mode: {agent.get_mode().upper()}]\n")
        return True

    elif c == "/personal":
        agent.mode = "personal"
        print(f"  [{AGENT_NAME} ab personal mode mein hai 💬]\n")
        return True

    elif c == "/professional":
        agent.mode = "professional"
        print(f"  [{AGENT_NAME} ab professional mode mein hai 💼]\n")
        return True

    elif c == "/reset":
        agent.reset_conversation()
        print(f"  [Conversation reset ho gayi]\n")
        return True

    elif c == "/memories":
        memories = list_all()
        if not memories:
            print("  [Koi memory nahi abhi tak]\n")
        else:
            print("  [Saved Memories]")
            for m in memories:
                print(f"  {m['category']}/{m['key']}: {m['value']}")
            print()
        return True

    elif c == "/remember":
        if len(parts) < 4:
            print("  Usage: /remember category key value")
            print("  Example: /remember academic cgpa 9.24\n")
        else:
            agent.save_fact(parts[1], parts[2], parts[3])
        return True

    return False


def main():
    print_banner()
    agent = LisaAgent()

    while True:
        try:
            user_input = input(f"{USER_NAME}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {AGENT_NAME}: Alvida! 👋\n")
            break

        if not user_input:
            continue

        # Check for commands
        if user_input.startswith("/"):
            result = handle_command(user_input, agent)
            if result == "EXIT":
                break
            continue

        # Normal chat
        reply = agent.chat(user_input)
        print(f"\n{AGENT_NAME}: {reply}\n")


if __name__ == "__main__":
    main()