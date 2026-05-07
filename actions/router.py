"""
LISA — Action Router (v2)
===========================
Change: whatsapp_message action ab conversation context pass karta hai
taaki LLM mood/tone/intention properly samjhe.
"""

from actions.intent_detector import detect_intent
from actions.system_actions  import (
    open_website, search_youtube, play_youtube,
    search_spotify, open_app, search_google,
    open_folder, open_file, system_command,
    smart_find_and_open,
)
from actions.whatsapp_actions import (
    whatsapp_send_message, whatsapp_send_file,
)

MIN_CONFIDENCE = 0.75

ACTION_MAP = {
    "open_website"      : open_website,
    "play_youtube"      : play_youtube,
    "search_youtube"    : search_youtube,
    "search_spotify"    : search_spotify,
    "open_app"          : open_app,
    "search_google"     : search_google,
    "open_folder"       : open_folder,
    "open_file"         : open_file,
    "find_file"         : smart_find_and_open,
    "whatsapp_message"  : whatsapp_send_message,
    "whatsapp_file"     : whatsapp_send_file,
    "system_command"    : system_command,
}

SPECIAL_PARAM_ACTIONS = {"find_file", "whatsapp_message", "whatsapp_file"}


def route_action(user_message: str, context=None) -> tuple[bool, str] | None:
    """
    user_message : jo Manish ne kaha
    context      : conversation history list — agent.py se pass karo.
                   Yahi LLM ko mood/tone/intention samajhne mein help karta hai.
    """
    intent     = detect_intent(user_message)
    action     = intent.get("action", "none")
    params     = intent.get("params", {})
    confidence = intent.get("confidence", 0.0)

    if action == "none" or confidence < MIN_CONFIDENCE:
        return None

    action_fn = ACTION_MAP.get(action)
    if not action_fn:
        return None

    # ── Special param handling ─────────────────────────────────────
    if action in SPECIAL_PARAM_ACTIONS:
        try:
            if action == "find_file":
                return action_fn(
                    query        = user_message,
                    folder       = params.get("folder", ""),
                    file         = params.get("file", ""),
                    on_main_screen = params.get("main_screen", False),
                )

            elif action == "whatsapp_message":
                return action_fn(
                    contact = params.get("contact", ""),
                    query   = user_message,        # full raw message — intent ke liye
                    message = params.get("message", ""),
                    context = context,             # ← YE NAYA: mood/tone ke liye
                )

            elif action == "whatsapp_file":
                return action_fn(
                    contact = params.get("contact", ""),
                    folder  = params.get("folder", ""),
                    file    = params.get("file", ""),
                    query   = user_message,
                    context = context,
                )

        except Exception as e:
            print(f"[Router] Error: {e}")
            return False, "action complete nahi hua"

    query = params.get("query", user_message)
    try:
        return action_fn(query)
    except Exception as e:
        print(f"[Router] Error: {e}")
        return False, "action complete nahi hua"