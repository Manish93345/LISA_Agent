"""
LISA — Main Agent (with Smart Memory)
"""

from config.settings import (
    MAX_HISTORY_TURNS, DEFAULT_MODE,
    MODE_PERSONAL, MODE_PROFESSIONAL,
    AGENT_NAME, USER_NAME
)
from config.prompts import (
    get_personal_prompt, get_professional_prompt,
    detect_mood, MODE_SWITCH_TRIGGERS
)
from core.llm_client        import get_response
from memory.rag_memory      import get_style_context, reset_recent
from memory.long_term       import get_all_memories, save_memory
from memory.memory_extractor import extract_and_save
from actions.router         import route_action

# Extract memory every N turns
EXTRACT_EVERY = 8

# Words that mean "yes" / "confirm" in Hinglish
CONFIRM_WORDS = {
    "haan", "haa", "ha", "yes", "yep", "yeah", "ok", "okay",
    "bhej do", "bhej de", "send karo", "send kar do", "kar do",
    "bol do", "likh do", "theek hai", "thik hai", "chalo", "done",
    "sure", "go ahead", "sahi hai", "bilkul",
}

# Words that mean "no" / "cancel"
CANCEL_WORDS = {
    "nahi", "nah", "no", "mat", "cancel", "ruk", "ruko",
    "mat bhejo", "mat karo", "chhod do", "rehne do", "band karo",
}


class LisaAgent:
    def __init__(self):
        self.mode                   = DEFAULT_MODE
        self.conversation_history   = []
        self.current_mood           = "neutral"
        self.turn_count             = 0
        self.pending_whatsapp       = None  # stores pending WhatsApp confirmation
        print(f"\n  {AGENT_NAME} initialized in {self.mode.upper()} mode\n")

    # ── Mode management ────────────────────────────────────────────────

    def _check_mode_switch(self, message: str) -> None:
        msg_lower = message.lower()
        for trigger in MODE_SWITCH_TRIGGERS["professional"]:
            if trigger in msg_lower:
                if self.mode != MODE_PROFESSIONAL:
                    self.mode = MODE_PROFESSIONAL
                    print(f"  [Mode -> PROFESSIONAL]")
                return
        for trigger in MODE_SWITCH_TRIGGERS["personal"]:
            if trigger in msg_lower:
                if self.mode != MODE_PERSONAL:
                    self.mode = MODE_PERSONAL
                    print(f"  [Mode -> PERSONAL]")
                return

    # ── System prompt ──────────────────────────────────────────────────

    def _build_system_prompt(self, user_message: str) -> str:
        self.current_mood = detect_mood(user_message)

        base = (
            get_personal_prompt(self.current_mood)
            if self.mode == MODE_PERSONAL
            else get_professional_prompt()
        )

        memories = get_all_memories()
        if memories:
            base += f"\n\n{memories}"

        rag_context = get_style_context(user_message, top_k=3)
        if rag_context:
            base += f"\n\n{rag_context}"

        return base

    # ── History ───────────────────────────────────────────────────────

    def _trim_history(self) -> None:
        max_msgs = MAX_HISTORY_TURNS * 2
        if len(self.conversation_history) > max_msgs:
            self.conversation_history = self.conversation_history[-max_msgs:]

    def _maybe_extract_memory(self) -> None:
        """Har EXTRACT_EVERY turns pe memory extract karo."""
        if self.turn_count > 0 and self.turn_count % EXTRACT_EVERY == 0:
            print(f"  [Memory] Extracting facts from conversation...")
            extract_and_save(self.conversation_history)

    # ── WhatsApp confirmation ─────────────────────────────────────────

    def _handle_whatsapp_confirm(self, user_message: str) -> str | None:
        """
        Agar koi pending WhatsApp action hai, toh user ka response check karo.
        Returns reply string if handled, None if not a confirmation situation.
        """
        if self.pending_whatsapp is None:
            return None

        msg_lower = user_message.lower().strip()

        # Check if user confirmed
        is_confirm = any(word in msg_lower for word in CONFIRM_WORDS)
        is_cancel  = any(word in msg_lower for word in CANCEL_WORDS)

        if is_cancel or (not is_confirm and not is_cancel):
            # Cancel or unrelated message -- clear pending and let normal flow handle
            if is_cancel:
                self.pending_whatsapp = None
                return "Okay jaan, cancel kar diya. Nahi bhejungi!"
            else:
                # Not a clear yes/no -- could be something else entirely
                # Clear pending and process normally
                self.pending_whatsapp = None
                return None

        # User confirmed -- execute the pending action
        pending = self.pending_whatsapp
        self.pending_whatsapp = None

        from actions.whatsapp_actions import whatsapp_confirm_and_send

        action_type = pending.get("type", "")
        contact     = pending.get("contact", "")
        content     = pending.get("content", "")

        success, result_msg = whatsapp_confirm_and_send(action_type, contact, content)

        if success:
            return f"Bhej diya jaan! {result_msg}"
        else:
            return f"Yaar bhej nahi paayi -- {result_msg}"

    def _check_whatsapp_confirmation(self, action_msg: str) -> tuple[bool, str] | None:
        """
        Check if action_msg is a WhatsApp confirmation request.
        If yes, store pending action and return confirmation prompt.
        """
        if not action_msg.startswith("CONFIRM_WHATSAPP_"):
            return None

        parts = action_msg.split("|")

        if action_msg.startswith("CONFIRM_WHATSAPP_MSG"):
            # Format: CONFIRM_WHATSAPP_MSG|contact|message
            if len(parts) >= 3:
                contact = parts[1]
                message = parts[2]
                self.pending_whatsapp = {
                    "type": "message",
                    "contact": contact,
                    "content": message,
                }
                return True, f"'{contact}' ko ye message bhejun: \"{message}\"? (haan/nahi)"

        elif action_msg.startswith("CONFIRM_WHATSAPP_FILE"):
            # Format: CONFIRM_WHATSAPP_FILE|contact|file_path|file_name
            if len(parts) >= 4:
                contact   = parts[1]
                file_path = parts[2]
                file_name = parts[3]
                self.pending_whatsapp = {
                    "type": "file",
                    "contact": contact,
                    "content": file_path,
                }
                return True, f"'{contact}' ko '{file_name}' bhejun WhatsApp pe? (haan/nahi)"

        return None

    # ── Main chat ─────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        if not user_message.strip():
            return ""

        self._check_mode_switch(user_message)
        self.turn_count += 1

        # Periodic memory extraction
        self._maybe_extract_memory()

        # ── Check if user is responding to WhatsApp confirmation ──────
        confirm_reply = self._handle_whatsapp_confirm(user_message)
        if confirm_reply is not None:
            self.conversation_history.append({"role": "user",      "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": confirm_reply})
            self._trim_history()
            return confirm_reply

        # Check for action
        action_result = route_action(user_message)

        system_prompt = self._build_system_prompt(user_message)

        if action_result is not None:
            success, action_msg = action_result

            # ── WhatsApp confirmation check ──────────────────────────
            wa_confirm = self._check_whatsapp_confirmation(action_msg)
            if wa_confirm is not None:
                _, confirm_prompt = wa_confirm
                # Let LLM phrase the confirmation naturally
                augmented = (
                    f"{user_message}\n\n"
                    f"[System: WhatsApp pe bhejne se pehle confirm karo. "
                    f"{confirm_prompt} "
                    f"Natural Hinglish mein poochho user se — short mein.]"
                )
                reply = get_response(system_prompt, self.conversation_history, augmented)
                self.conversation_history.append({"role": "user",      "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": reply})
                self._trim_history()
                return reply

            status = "successfully completed" if success else "failed"
            augmented = (
                f"{user_message}\n\n"
                f"[System: Action {status} -- {action_msg}. "
                f"Natural tone mein confirm karo, short response.]"
            )
            reply = get_response(system_prompt, self.conversation_history, augmented)
        else:
            reply = get_response(system_prompt, self.conversation_history, user_message)

        self.conversation_history.append({"role": "user",      "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": reply})
        self._trim_history()

        return reply

    # ── Session end ───────────────────────────────────────────────────

    def end_session(self) -> None:
        """
        Session band hone par call karo — final memory extract hoga.
        main.py aur voice_main.py mein /quit pe ye call hoga.
        """
        # Close WhatsApp browser if open
        try:
            from actions.whatsapp_actions import close_driver
            close_driver()
        except Exception:
            pass

        if len(self.conversation_history) >= 4:
            print(f"\n  [Memory] Session khatam -- facts save kar rhi hoon...")
            saved = extract_and_save(self.conversation_history)
            print(f"  [Memory] {saved} facts saved.")

    # ── Utilities ─────────────────────────────────────────────────────

    def save_fact(self, category: str, key: str, value: str) -> None:
        save_memory(category, key, value)
        print(f"  [Memory saved] {category}/{key}: {value}")

    def get_mode(self)  -> str: return self.mode
    def get_mood(self)  -> str: return self.current_mood

    def reset_conversation(self) -> None:
        self.conversation_history = []
        self.turn_count           = 0
        self.pending_whatsapp     = None
        reset_recent()
        print("  [Conversation reset]")