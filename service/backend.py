"""
backend.py — one interface, two ways to run the model, so nothing upstream cares
which is live. Flip by setting env vars (see .env.example):

    LOCAL  : MODEL_BASE_URL + MODEL_NAME   -> self-hosted Qwen3 / Llama via vLLM
             (nothing leaves the machine — the right posture once we're sensing
              behavior for real)
    API    : ANTHROPIC_API_KEY / OPENAI_API_KEY -> Claude / GPT
             (fastest to iterate; data leaves the machine)
    (none) : deterministic fallback strings from orchestration.py, so the whole
             system runs in tests with no key and no GPU.

vLLM speaks the OpenAI wire format, so local and OpenAI collapse into the same
client. That's the whole trick — the "local vs API" choice is one line of config,
not a code path.
"""

from __future__ import annotations
import os
from typing import Optional


class Backend:
    def __init__(self):
        self.mode = self._detect()

    def _detect(self) -> str:
        if os.getenv("MODEL_BASE_URL"):
            return "local"
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return "fallback"

    def complete(self, messages: list[dict], max_tokens: int = 120) -> Optional[str]:
        """Return the model's text, or None to signal 'use the fallback'."""
        try:
            if self.mode in ("local", "openai"):
                return self._openai_compatible(messages, max_tokens)
            if self.mode == "anthropic":
                return self._anthropic(messages, max_tokens)
        except Exception as e:  # never let a model hiccup reach the student
            print(f"[backend] {self.mode} call failed, falling back: {e}")
        return None

    # local (vLLM) and OpenAI share this exact path
    def _openai_compatible(self, messages, max_tokens):
        from openai import OpenAI
        client = OpenAI(
            base_url=os.getenv("MODEL_BASE_URL"),   # None -> real OpenAI
            api_key=os.getenv("OPENAI_API_KEY", "sk-local-unused"),
        )
        model = os.getenv("MODEL_NAME", "gpt-4o-mini")
        r = client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens, temperature=0.6)
        return r.choices[0].message.content

    def _anthropic(self, messages, max_tokens):
        import anthropic
        client = anthropic.Anthropic()
        # Anthropic takes a single top-level `system`, but callers may pass several
        # system messages (persona + code-context note). Merge them, or the extra
        # context is silently dropped.
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        turns = [m for m in messages if m["role"] != "system"]
        r = client.messages.create(
            model=os.getenv("MODEL_NAME", "claude-sonnet-5"),
            system=system, messages=turns, max_tokens=max_tokens)
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
