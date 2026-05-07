"""
LISA — Smart WhatsApp Send Action (v2)
========================================
Changes:
  - smart_whatsapp_send ab (bool, str) tuple return karta hai
    agent.py ko yahi chahiye tha
  - Auto-learn: naye contacts automatically contacts.json mein save
  - Relationship guess: naam se detect (papa/bhai/etc)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings

CONTACTS_FILE = BASE_DIR / "data" / "contacts.json"


# ══════════════════════════════════════════════════════════════════════
#  CONTACTS
# ══════════════════════════════════════════════════════════════════════

def _load_contacts() -> dict:
    if CONTACTS_FILE.exists():
        with open(CONTACTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("contacts", {})
    return {}


def get_contact_info(name: str) -> dict:
    contacts = _load_contacts()
    name_lower = name.lower().strip()
    if name_lower in contacts:
        return contacts[name_lower]
    for key, info in contacts.items():
        if name_lower in key or key in name_lower:
            return info
    return {"full_name": name.title(), "relationship": "default"}


def _guess_relationship(name: str) -> str:
    """Naam se relationship guess karo."""
    n = name.lower()
    elder  = {"papa", "dad", "pita", "mummy", "mom", "maa", "mama", "chacha",
               "chachi", "nana", "nani", "dada", "dadi", "uncle", "aunty",
               "mausi", "mausa", "taau", "taai"}
    family = {"bhai", "brother", "behen", "sister", "didi", "bhaiya", "sis"}
    if any(k in n for k in elder):
        return "elder_family"
    if any(k in n for k in family):
        return "family"
    return "friend"


def auto_learn_contact(name: str, relationship: str, full_name: str = "") -> None:
    """Naya contact contacts.json mein save karo — dobara poochhna nahi padega."""
    try:
        if CONTACTS_FILE.exists():
            with open(CONTACTS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"contacts": {}}

        key = name.lower().strip()
        if key not in data.get("contacts", {}):
            data.setdefault("contacts", {})[key] = {
                "full_name"    : full_name or name.title(),
                "relationship" : relationship,
                "auto_learned" : True,
            }
            CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [Contacts] '{name}' auto-save ({relationship})")
    except Exception as e:
        print(f"  [Contacts] Save error: {e}")


# ══════════════════════════════════════════════════════════════════════
#  TONE PROMPTS
# ══════════════════════════════════════════════════════════════════════

TONE_PROMPTS = {
    "friend": """
Tu LISA hai — Manish ki AI assistant.
Ek dost ki taraf se WhatsApp message likhna hai.
Tone: casual, friendly Hinglish (Hindi + English mix).
2-3 lines max. Yaar-dost wala style, seedha baat.
Example: "Bhai, computer graphics ke notes hai toh bhej de yaar, exam aa rha hai 🙏"
""",
    "elder_family": """
Tu LISA hai — Manish ki AI assistant.
Ek bete ki taraf se Papa/Mama ya kisi bade ko message likhna hai.
Tone: respectful warm Hindi. "Aap" use karo, "tum" nahi.
2-3 lines. Formal nahi but respectful zaroor.
Example: "Papa, namaste 🙏 Kal ghar aa sakta hoon kya? Kuch baat karni thi."
""",
    "family": """
Tu LISA hai — Manish ki AI assistant.
Family member (Bhai/Behen) ko message likhna hai.
Tone: warm, casual Hindi/Hinglish. Close family feel.
2-3 lines max.
""",
    "senior": """
Tu LISA hai — Manish ki AI assistant.
Ek senior/professor/sir ko professional message likhna hai.
Tone: formal respectful English ya Hindi. "Sir/Ma'am" use karo.
Short aur to-the-point.
""",
    "colleague": """
Tu LISA hai — Manish ki AI assistant.
College/office colleague ko message likhna hai.
Tone: semi-formal friendly Hinglish. 2-3 lines.
""",
    "default": """
Tu LISA hai — Manish ki AI assistant.
WhatsApp message likhna hai. Tone: neutral polite Hinglish.
Chhota aur clear rakho.
""",
}


# ══════════════════════════════════════════════════════════════════════
#  LLM DRAFTER
# ══════════════════════════════════════════════════════════════════════

def draft_message(contact_name: str, intent: str, relationship: str) -> str:
    tone_prompt = TONE_PROMPTS.get(relationship, TONE_PROMPTS["default"])
    user_prompt = (
        f"Contact: {contact_name}\n"
        f"Ye convey karna hai: {intent}\n\n"
        f"Sirf WhatsApp message text likho — koi explanation nahi, koi quotes nahi."
    )
    provider = settings.LLM_PROVIDER

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=[
                {"role": "system", "content": tone_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=200, temperature=0.7,
        )
        return resp.choices[0].message.content.strip()

    elif provider == "cerebras":
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=settings.CEREBRAS_API_KEY)
        resp = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=[
                {"role": "system", "content": tone_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()

    elif provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        resp = client.messages.create(
            model=settings.CHAT_MODEL,
            system=tone_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=200,
        )
        return resp.content[0].text.strip()

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash",
                                       system_instruction=tone_prompt)
        return model.generate_content(user_prompt).text.strip()

    else:
        raise ValueError(f"Unknown provider: {provider}")


# ══════════════════════════════════════════════════════════════════════
#  MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════

def smart_whatsapp_send(
    contact: str,
    intent: str,
    wa_driver=None,
    relationship: str = "",
) -> tuple:
    """
    Full flow: draft → confirm → send.

    Returns tuple (bool, str) — agent.py ko yahi chahiye.
      (True,  "Message bhej diya!")
      (False, "reason")
    """

    # ── Contact info ──────────────────────────────────────────────────
    info      = get_contact_info(contact)
    full_name = info.get("full_name", contact.title())

    rel = (relationship
           or (info.get("relationship") if info.get("relationship") != "default" else "")
           or _guess_relationship(contact))

    # Auto-learn naye contacts
    if not info or info.get("relationship", "default") == "default":
        auto_learn_contact(contact, rel, full_name)

    print(f"\n  [Lisa] '{full_name}' ko message draft kar rhi hoon...")
    print(f"  [Lisa] Tone: {rel}")

    # ── Draft ─────────────────────────────────────────────────────────
    try:
        drafted = draft_message(full_name, intent, rel)
    except Exception as e:
        return (False, f"Draft error: {e}")

    # ── Preview + Confirm ─────────────────────────────────────────────
    print(f"\n  ┌─ Drafted Message — {full_name} {'─'*20}")
    for line in drafted.split('\n'):
        print(f"  │  {line}")
    print(f"  └{'─'*45}")

    confirm = input("\n  Ye message bhejun? (y/n/e): ").strip().lower()

    if confirm == 'n':
        return (False, "Cancel kar diya")

    if confirm == 'e':
        print("  Apna message likho (blank line press karo done ke liye):")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        drafted = '\n'.join(lines[:-1]) if lines else drafted
        if input("  Ab bhejun? (y/n): ").strip().lower() != 'y':
            return (False, "Cancel kar diya")

    # ── Send ──────────────────────────────────────────────────────────
    from actions.whatsapp_actions import WhatsAppDriver

    driver_created = False
    if wa_driver is None:
        wa_driver = WhatsAppDriver()
        if not wa_driver.start():
            return (False, "Browser start nahi hua")
        driver_created = True

    try:
        orig = settings.WHATSAPP_CONFIRM_SEND
        settings.WHATSAPP_CONFIRM_SEND = False

        if not wa_driver.search_and_open_contact(contact):
            return (False, f"'{contact}' WhatsApp pe nahi mila")

        sent = wa_driver.send_message(drafted)
        settings.WHATSAPP_CONFIRM_SEND = orig

        if sent:
            return (True, f"{full_name} ko message bhej diya ✓")
        return (False, "Send fail")

    finally:
        if driver_created:
            wa_driver.close()


# ══════════════════════════════════════════════════════════════════════
#  INTENT PARSER
# ══════════════════════════════════════════════════════════════════════

def parse_whatsapp_intent(user_text: str) -> dict | None:
    import re
    text_lower = user_text.lower()
    patterns = [
        r'(\w+)\s+ko\s+(?:message|msg|whatsapp)\s+(?:kar|karo|bhejo|bhej|dena|do)\s+(?:ki|ke liye|na ki)?\s*(.*)',
        r'(?:message|msg)\s+(?:kar|karo|bhejo)\s+(\w+)\s+ko\s+(?:ki|ke liye)?\s*(.*)',
        r'(\w+)\s+ko\s+(?:bolo|bol)\s+(.*)',
        r'(\w+)\s+ko\s+(?:likh|likho|type kar)\s+(.*)',
    ]
    skip = {"ek", "yeh", "wo", "woh", "mujhe", "mera", "meri", "apne", "aap"}
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            contact = m.group(1).strip()
            intent  = m.group(2).strip() if m.group(2) else ""
            if contact not in skip:
                return {"contact": contact, "intent": intent or user_text}
    return None


# ══════════════════════════════════════════════════════════════════════
#  STANDALONE TEST
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "="*55)
    print("   LISA — Smart WhatsApp Send (v2)")
    print("="*55)

    user_input = input("\n  Kya kehna hai Lisa se: ").strip()
    parsed = parse_whatsapp_intent(user_input)

    if parsed:
        print(f"  Contact: {parsed['contact']} | Intent: {parsed['intent']}")
        ok, msg = smart_whatsapp_send(parsed["contact"], parsed["intent"])
        print(f"\n  Result: {'✓' if ok else '✗'} — {msg}")
    else:
        contact = input("  Contact naam: ").strip()
        intent  = input("  Kya kehna hai: ").strip()
        ok, msg = smart_whatsapp_send(contact, intent)
        print(f"\n  Result: {'✓' if ok else '✗'} — {msg}")