"""
LISA — Action Router
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

# Actions that need special param handling (not just "query")
SPECIAL_PARAM_ACTIONS = {"find_file", "whatsapp_message", "whatsapp_file"}


def route_action(user_message: str) -> tuple[bool, str] | None:
    intent     = detect_intent(user_message)
    action     = intent.get("action", "none")
    params     = intent.get("params", {})
    confidence = intent.get("confidence", 0.0)

    if action == "none" or confidence < MIN_CONFIDENCE:
        return None

    action_fn = ACTION_MAP.get(action)
    if not action_fn:
        return None

    # ── Special param handling for complex actions ────────────────
    if action in SPECIAL_PARAM_ACTIONS:
        try:
            if action == "find_file":
                folder         = params.get("folder", "")
                file           = params.get("file", "")
                on_main_screen = params.get("main_screen", False)
                return action_fn(query=user_message, folder=folder, file=file, on_main_screen=on_main_screen)

            elif action == "whatsapp_message":
                contact = params.get("contact", "")
                message = params.get("message", "")
                return action_fn(query=user_message, contact=contact, message=message)

            elif action == "whatsapp_file":
                contact = params.get("contact", "")
                folder  = params.get("folder", "")
                file    = params.get("file", "")
                return action_fn(query=user_message, contact=contact, folder=folder, file=file)

        except Exception as e:
            print(f"[Router] Error: {e}")
            return False, "action complete nahi hua"

    query = params.get("query", user_message)
    try:
        return action_fn(query)
    except Exception as e:
        print(f"[Router] Error: {e}")
        return False, "action complete nahi hua"