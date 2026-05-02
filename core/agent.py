"""
LISA — Main Agent (with mood detection + diversity fix)
"""

from config.settings import (
    MAX_HISTORY_TURNS, DEFAULT_MODE,
    MODE_PERSONAL, MODE_PROFESSIONAL,
    AGENT_NAME, USER_NAME
)
from config.prompts import (
    get_personal_prompt,
    get_professional_prompt,
    detect_mood,
    MODE_SWITCH_TRIGGERS
)
from core.llm_client   import get_response
from memory.rag_memory import get_style_context, reset_recent
from memory.long_term  import get_all_memories, save_memory


class LisaAgent:
    def __init__(self):
        self.mode                 = DEFAULT_MODE
        self.conversation_history = []
        self.current_mood         = "neutral"
        print(f"\n  {AGENT_NAME} initialized in {self.mode.upper()} mode\n")

    # ── Mode management ────────────────────────────────────────────────

    def _check_mode_switch(self, message: str) -> None:
        msg_lower = message.lower()
        for trigger in MODE_SWITCH_TRIGGERS["professional"]:
            if trigger in msg_lower:
                if self.mode != MODE_PROFESSIONAL:
                    self.mode = MODE_PROFESSIONAL
                    print(f"  [Mode → PROFESSIONAL]")
                return
        for trigger in MODE_SWITCH_TRIGGERS["personal"]:
            if trigger in msg_lower:
                if self.mode != MODE_PERSONAL:
                    self.mode = MODE_PERSONAL
                    print(f"  [Mode → PERSONAL]")
                return

    # ── Memory auto-detection ──────────────────────────────────────────

    def _detect_and_save_memory(self, message: str) -> None:
        import re
        msg_lower = message.lower()

        # CGPA / marks
        cgpa_match = re.search(
            r'(cgpa|gpa|marks?|score)\s*[:\-]?\s*(\d+\.?\d*)', msg_lower
        )
        if cgpa_match:
            save_memory("academic", "cgpa", cgpa_match.group(0))

        # Semester
        sem_match = re.search(r'sem(?:ester)?\s*(\d+)', msg_lower)
        if sem_match:
            save_memory("academic", "current_semester",
                        f"Semester {sem_match.group(1)}")

        # Incidents — agar Manish koi badi baat bataye
        incident_triggers = [
            "hua tha", "ho gaya", "ho gayi", "unfriend", "breakup",
            "fight", "accident", "result aaya", "clear ho gaya"
        ]
        for trigger in incident_triggers:
            if trigger in msg_lower and len(message) > 40:
                # Save first 120 chars as incident note
                save_memory(
                    "incident",
                    f"incident_{len(message) % 1000}",
                    message[:120]
                )
                break

    # ── System prompt builder ──────────────────────────────────────────

    def _build_system_prompt(self, user_message: str) -> str:
        # Detect mood
        self.current_mood = detect_mood(user_message)

        # Base personality
        if self.mode == MODE_PERSONAL:
            base = get_personal_prompt(self.current_mood)
        else:
            base = get_professional_prompt()

        # Long-term memory
        memories = get_all_memories()
        if memories:
            base += f"\n\n{memories}"

        # RAG context
        rag_context = get_style_context(user_message, top_k=4)
        if rag_context:
            base += f"\n\n{rag_context}"

        return base

    # ── History management ─────────────────────────────────────────────

    def _trim_history(self) -> None:
        max_msgs = MAX_HISTORY_TURNS * 2
        if len(self.conversation_history) > max_msgs:
            self.conversation_history = self.conversation_history[-max_msgs:]

    # ── Main chat ─────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        if not user_message.strip():
            return ""

        self._check_mode_switch(user_message)
        self._detect_and_save_memory(user_message)

        system_prompt = self._build_system_prompt(user_message)

        reply = get_response(
            system_prompt        = system_prompt,
            conversation_history = self.conversation_history,
            user_message         = user_message
        )

        self.conversation_history.append(
            {"role": "user",      "content": user_message}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": reply}
        )
        self._trim_history()

        return reply

    # ── Utilities ─────────────────────────────────────────────────────

    def save_fact(self, category: str, key: str, value: str) -> None:
        save_memory(category, key, value)
        print(f"  [Memory saved] {category}/{key}: {value}")

    def get_mode(self) -> str:
        return self.mode

    def get_mood(self) -> str:
        return self.current_mood

    def reset_conversation(self) -> None:
        self.conversation_history = []
        reset_recent()   # RAG recent list bhi clear karo
        print("  [Conversation reset]")