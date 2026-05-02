"""
LISA — Main Entry Point
========================
Usage:
    cd D:\\Study\\LISA_Agent
    python main.py

Commands:
    /mode         → current mode + mood dekho
    /personal     → personal mode
    /professional → professional mode
    /remember category key value → manually kuch yaad karao
    /memories     → saari memories dekho
    /reset        → conversation reset
    /quit         → exit
"""

from core.agent       import LisaAgent
from memory.long_term import list_all
from config.settings  import AGENT_NAME, USER_NAME


def print_banner():
    print("\n" + "="*55)
    print(f"   {AGENT_NAME.upper()} — Personal AI Agent")
    print("="*55)
    print(f"   Namaste {USER_NAME}! Main {AGENT_NAME} hoon.")
    print(f"   Type /quit to exit | /mode to check status")
    print("="*55 + "\n")


def handle_command(cmd: str, agent: LisaAgent):
    parts = cmd.strip().split(maxsplit=3)
    c     = parts[0].lower()

    if c == "/quit":
        print(f"\n  {AGENT_NAME}: Theek hai, alvida! Take care. 👋\n")
        return "EXIT"

    elif c == "/mode":
        print(f"  [Mode: {agent.get_mode().upper()} | Mood detected: {agent.get_mood()}]\n")
        return True

    elif c == "/personal":
        agent.mode = "personal"
        print(f"  [{AGENT_NAME} ab personal mode mein hai]\n")
        return True

    elif c == "/professional":
        agent.mode = "professional"
        print(f"  [{AGENT_NAME} ab professional mode mein hai]\n")
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

        if user_input.startswith("/"):
            result = handle_command(user_input, agent)
            if result == "EXIT":
                break
            continue

        reply = agent.chat(user_input)
        print(f"\n{AGENT_NAME}: {reply}\n")


if __name__ == "__main__":
    main()