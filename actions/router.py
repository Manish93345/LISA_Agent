"""
LISA — Action Router
"""

from actions.intent_detector import detect_intent
from actions.system_actions  import (
    open_website, search_youtube, play_youtube,
    search_spotify, open_app, search_google,
    open_folder, open_file, system_command,
)

MIN_CONFIDENCE = 0.75

ACTION_MAP = {
    "open_website"   : open_website,
    "play_youtube"   : play_youtube,     # seedha video play
    "search_youtube" : search_youtube,   # sirf search
    "search_spotify" : search_spotify,
    "open_app"       : open_app,
    "search_google"  : search_google,
    "open_folder"    : open_folder,
    "open_file"      : open_file,
    "system_command" : system_command,
}


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

    query = params.get("query", user_message)
    try:
        return action_fn(query)
    except Exception as e:
        print(f"[Router] Error: {e}")
        return False, "action complete nahi hua"