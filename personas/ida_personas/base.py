"""
base.py — the shared IDA persona. Each of the four personas is a thin subclass
that sets its name, avatar, and voice; everything else (the tone rules every IDA
persona obeys, calling the model, the fallback) lives here.

These are NATIVE Jupyter AI personas: they subclass BasePersona, are registered
via entry points, and are @-mentioned in the chat. That means they're the
ON-DEMAND side of IDA — the student invokes them. The proactive side (noticing
without being asked) is the separate delivery service in ../service, which reuses
the same four voices. Same personalities, two ways in.
"""
from __future__ import annotations
import os

from jupyter_ai_persona_manager import BasePersona, PersonaDefaults
from jupyterlab_chat.models import Message

from .model import complete

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

# The rules EVERY IDA persona obeys, regardless of which one you're talking to.
# Same spirit as service/orchestration.py PERSONA, kept here as the source of truth.
SHARED_RULES = """You are IDA, a quiet study companion inside a student's coding editor.
You are talking with a neurodivergent student in a programming course; some of these
students distrust "soft" support and are sensitive to anything that feels like
judgement. So, always:
- Describe the situation on screen; never label the student's feelings.
- Keep it to one or two short sentences. Offer one small, concrete, optional next step.
- No "you should", no empty praise, no exclamation marks, no therapy-speak.
- Make it effortless to ignore. If unsure, say less."""


class IdaBasePersona(BasePersona):
    # subclasses set these
    SUPPORT = "none"       # which behavioral state this persona serves
    NAME = "IDA"
    DESCRIPTION = ""
    AVATAR = "unblock.svg"
    VOICE = ""             # persona-specific framing, prepended to SHARED_RULES

    @property
    def defaults(self) -> PersonaDefaults:
        return PersonaDefaults(
            name=self.NAME,
            description=self.DESCRIPTION,
            avatar_path=os.path.join(ASSETS, self.AVATAR),
            system_prompt=self.system_prompt(),
        )

    def system_prompt(self) -> str:
        return f"{self.VOICE}\n\n{SHARED_RULES}"

    async def process_message(self, message: Message):
        reply = complete(self.system_prompt(), message.body) or self.fallback()
        self.send_message(reply)

    def fallback(self) -> str:
        """Used when no model is configured, so the persona still responds."""
        return "I'm here — tell me which cell or error you're looking at and we'll take it one step at a time."
