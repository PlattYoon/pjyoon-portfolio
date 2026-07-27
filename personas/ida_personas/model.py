"""
model.py — how an IDA persona talks to a model. Standalone (no Jupyter import) so
it's testable on its own and the package stays self-contained.

Mirrors the service's backend: one interface over local vLLM (Qwen3/Llama),
the APIs (Claude/GPT), and a graceful fallback when there's no key/GPU.
"""
from __future__ import annotations
import os


def _mode() -> str:
    if os.getenv("MODEL_BASE_URL"):
        return "local"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "fallback"


def complete(system: str, user: str, max_tokens: int = 220) -> str | None:
    """Return the model's reply, or None to signal 'use the persona's fallback'."""
    mode = _mode()
    try:
        if mode in ("local", "openai"):
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("MODEL_BASE_URL"),
                            api_key=os.getenv("OPENAI_API_KEY", "sk-local-unused"))
            r = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                max_tokens=max_tokens, temperature=0.6)
            return r.choices[0].message.content
        if mode == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            r = client.messages.create(
                model=os.getenv("MODEL_NAME", "claude-sonnet-4-6"),
                system=system, max_tokens=max_tokens,
                messages=[{"role": "user", "content": user}])
            return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    except Exception as e:
        print(f"[ida_personas.model] {mode} call failed, using fallback: {e}")
    return None
