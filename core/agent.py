"""
LISA — Main Agent (with Smart Memory + WhatsApp Confirmation Flow)
"""

import threading

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
    "sure", "go ahead", "sahi hai", "bilkul", "haanji", "ji haan",
    "approve", "approved", "confirm", "confirmed", "send",
}

# Words that mean "no" / "cancel"
CANCEL_WORDS = {
    "nahi", "nah", "no", "mat bhejo", "mat karo", "cancel", "ruk", "ruko",
    "chhod do", "rehne do", "band karo", "stop", "abort", "reject",
    "rehne", "rukk", "nope",
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
        if self.turn_count > 0 and self.turn_count % EXTRACT_EVERY == 0:
            print(f"  [Memory] Extracting facts from conversation...")
            extract_and_save(self.conversation_history)

    # ── WhatsApp confirmation ─────────────────────────────────────────

    def _is_confirm(self, msg: str) -> bool:
        m = msg.lower().strip()
        # Exact match check (avoid "nahi" matching "haan nahi")
        words = m.split()
        for w in words:
            if w in CONFIRM_WORDS:
                # Also check no cancel word in msg
                if not any(c in m for c in CANCEL_WORDS):
                    return True
        # Phrase check
        for phrase in CONFIRM_WORDS:
            if " " in phrase and phrase in m:
                if not any(c in m for c in CANCEL_WORDS):
                    return True
        return False

    def _is_cancel(self, msg: str) -> bool:
        m = msg.lower().strip()
        for w in m.split():
            if w in CANCEL_WORDS:
                return True
        for phrase in CANCEL_WORDS:
            if " " in phrase and phrase in m:
                return True
        return False

    def _handle_whatsapp_confirm(self, user_message: str):
        """
        Pending WhatsApp action ho toh user response process karo.
        Returns reply string if handled, None otherwise.
        """
        if self.pending_whatsapp is None:
            return None

        # User wants to EDIT the draft? e.g. "isme add kar do ki..."
        # For now we treat any non-confirm/non-cancel as cancellation of pending
        # so user can re-issue the request properly.

        if self._is_cancel(user_message):
            self.pending_whatsapp = None
            return "Theek hai jaan, cancel kar diya. Nahi bhejungi."

        if not self._is_confirm(user_message):
            # Not a clear yes/no -- could be edit request or unrelated
            # Clear pending and let normal flow handle
            self.pending_whatsapp = None
            return None

        # User confirmed -- execute pending action in background
        pending = self.pending_whatsapp
        self.pending_whatsapp = None

        from actions.whatsapp_actions import whatsapp_confirm_and_send

        action_type = pending.get("type", "")
        contact     = pending.get("contact", "")
        content     = pending.get("content", "")

        # Background thread mein send karo taaki UI block na ho
        result_holder = {"success": False, "msg": "send mein time lag rha hai..."}
        done_event = threading.Event()

        def _do_send():
            try:
                s, m = whatsapp_confirm_and_send(action_type, contact, content)
                result_holder["success"] = s
                result_holder["msg"]     = m
            except Exception as e:
                result_holder["msg"] = f"error: {e}"
            finally:
                done_event.set()

        t = threading.Thread(target=_do_send, daemon=True)
        t.start()

        # Wait time: messages = 20s, files = 45s (file upload takes longer)
        timeout = 45 if action_type == "file" else 20
        done_event.wait(timeout=timeout)

        if result_holder["success"]:
            return f"Bhej diya jaan! {result_holder['msg']}"
        elif done_event.is_set():
            return f"Yaar bhej nahi paayi -- {result_holder['msg']}"
        else:
            return "Send kar rhi hoon background mein, ho jayega thodi der mein."

    def _check_whatsapp_confirmation(self, action_msg: str):
        """
        Check if action_msg is a WhatsApp confirmation request.
        If yes, store pending action and return confirmation prompt.
        """
        if not action_msg.startswith("CONFIRM_WHATSAPP_"):
            return None

        parts = action_msg.split("|")

        if action_msg.startswith("CONFIRM_WHATSAPP_MSG"):
            if len(parts) >= 3:
                contact = parts[1]
                # Message may contain | -- rejoin remaining parts
                message = "|".join(parts[2:])
                self.pending_whatsapp = {
                    "type": "message",
                    "contact": contact,
                    "content": message,
                }
                return True, contact, message, "message"

        elif action_msg.startswith("CONFIRM_WHATSAPP_FILE"):
            if len(parts) >= 4:
                contact   = parts[1]
                file_path = parts[2]
                file_name = parts[3]
                self.pending_whatsapp = {
                    "type": "file",
                    "contact": contact,
                    "content": file_path,
                }
                return True, contact, file_name, "file"

        return None

    # ── Main chat ─────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        if not user_message.strip():
            return ""

        self._check_mode_switch(user_message)
        self.turn_count += 1

        # Periodic memory extraction
        self._maybe_extract_memory()

        # ── Step 1: Check if user is responding to WhatsApp confirmation ──
        confirm_reply = self._handle_whatsapp_confirm(user_message)
        if confirm_reply is not None:
            self.conversation_history.append({"role": "user",      "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": confirm_reply})
            self._trim_history()
            return confirm_reply

        # ── Step 2: Detect & route action ──
        action_result = route_action(user_message, context=self.conversation_history)
        system_prompt = self._build_system_prompt(user_message)

        if action_result is not None:
            success, action_msg = action_result

            # ── WhatsApp confirmation flow ──
            wa_confirm = self._check_whatsapp_confirmation(action_msg)
            if wa_confirm is not None:
                _, contact, content, kind = wa_confirm

                if kind == "message":
                    # Show the drafted message clearly + ask confirmation
                    augmented = (
                        f"{user_message}\n\n"
                        f"[System: WhatsApp message draft kiya hai '{contact}' ke liye:\n"
                        f"\"{content}\"\n"
                        f"User se confirmation maango -- short, natural Hinglish mein. "
                        f"Pehle draft dikhao, fir poochho 'send kar du?'. "
                        f"Apni taraf se kuch add mat karo, jo draft hai bas wahi dikhao.]"
                    )
                else:  # file
                    augmented = (
                        f"{user_message}\n\n"
                        f"[System: WhatsApp pe '{contact}' ko '{content}' file bhejni hai. "
                        f"User se confirm maango -- short Hinglish.]"
                    )

                reply = get_response(system_prompt, self.conversation_history, augmented)
                self.conversation_history.append({"role": "user",      "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": reply})
                self._trim_history()
                return reply

            # ── Normal action result ──
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
