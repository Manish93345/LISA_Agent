"""
LISA — Main Agent (Orchestrator)
"""

from config.settings import (
    MAX_HISTORY_TURNS, DEFAULT_MODE,
    MODE_PERSONAL, MODE_PROFESSIONAL,
    AGENT_NAME, USER_NAME
)
from config.prompts import (
    PERSONAL_SYSTEM_PROMPT,
    PROFESSIONAL_SYSTEM_PROMPT,
    MODE_SWITCH_TRIGGERS
)
from core.llm_client   import get_response
from memory.rag_memory import get_style_context
from memory.long_term  import get_all_memories, save_memory


class LisaAgent:
    def __init__(self):
        self.mode: str              = DEFAULT_MODE
        self.conversation_history   = []   # list of {"role": "user"/"assistant", "content": "..."}
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

        cgpa_match = re.search(r'(cgpa|gpa|marks?|score)\s*[:\-]?\s*(\d+\.?\d*)', msg_lower)
        if cgpa_match:
            save_memory("academic", "cgpa", cgpa_match.group(0))

        sem_match = re.search(r'sem(?:ester)?\s*(\d+)', msg_lower)
        if sem_match:
            save_memory("academic", "current_semester", f"Semester {sem_match.group(1)}")

    # ── System prompt builder ──────────────────────────────────────────

    def _build_system_prompt(self, user_message: str) -> str:
        base = (
            PERSONAL_SYSTEM_PROMPT
            if self.mode == MODE_PERSONAL
            else PROFESSIONAL_SYSTEM_PROMPT
        )

        memories = get_all_memories()
        if memories:
            base += f"\n\n{memories}"

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

        # Save to history (Groq format)
        self.conversation_history.append({"role": "user",      "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": reply})
        self._trim_history()

        return reply

    # ── Utilities ─────────────────────────────────────────────────────

    def save_fact(self, category: str, key: str, value: str) -> None:
        save_memory(category, key, value)
        print(f"  [Memory saved] {category}/{key}: {value}")

    def get_mode(self) -> str:
        return self.mode

    def reset_conversation(self) -> None:
        self.conversation_history = []
        print("  [Conversation reset]")