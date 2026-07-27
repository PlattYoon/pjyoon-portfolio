"""
eval_models.py — the harness for the "which model?" question the team keeps
deferring (Llama vs Qwen3 vs an API). Runs a fixed set of programming-frustration
scenarios through the pipeline and reports, per scenario:

  - latency (the local-vs-API tradeoff Darren cares about)
  - the actual message produced (so a human can rate empathy/tone — the part that
    matters most and that no automatic metric captures)
  - automatic guardrail checks: is it short? does it describe the situation instead
    of labeling the person? no exclamation-mark cheerfulness?

Run:
  python eval_models.py                 # whatever backend .env selects (fallback if none)
  ANTHROPIC_API_KEY=... python eval_models.py
  MODEL_BASE_URL=http://localhost:8000/v1 MODEL_NAME=Qwen3-32B python eval_models.py

This does NOT pick a winner for you — tone is a human call. It lays the candidates
side by side so the team can decide with evidence instead of vibes.
"""

from __future__ import annotations
import time
from signals import (Event, infer, State, cell_run, idle, edit_churn,
                     file_switch, help_opened, task_abandon, frustration_signal)
from orchestration import build_prompt, to_message, FALLBACKS
from backend import Backend

T = 1_000_000.0

# each scenario: a name, an event trace, and the state we expect it to land in
SCENARIOS = [
    ("stuck: same error x4",
     [cell_run(T + i, "error", "NameError", "c3", consecutive_failures=i + 1) for i in range(4)]
     + [help_opened(T + 5)], State.STUCK),
    ("overwhelmed: churn across cells",
     [edit_churn(T, 10, 200), edit_churn(T + 5, 5, 150),
      cell_run(T + 6, "error", "ValueError", "a"),
      cell_run(T + 7, "error", "KeyError", "b"),
      file_switch(T + 8, "other.ipynb", 3000), help_opened(T + 9)], State.OVERWHELMED),
    ("withdrawn: struggle, no help, leaves",
     [cell_run(T, "error", "TypeError", "z", consecutive_failures=1),
      cell_run(T + 4, "error", "TypeError", "z", consecutive_failures=2),
      task_abandon(T + 8, "hw2")], State.WITHDRAWN),
    ("stuck + Michael's frustration signal",
     [cell_run(T + i, "error", "NameError", "c3", consecutive_failures=i + 1) for i in range(4)]
     + [help_opened(T + 5), frustration_signal(T + 4, 0.9)], State.STUCK),
]

# guardrails from orchestration.py's tone rules, as automatic checks
BANNED = ["you seem", "you're feeling", "you are feeling", "you look", "you appear",
          "frustrated", "anxious", "overwhelmed"]  # labeling the person, not the situation

def guardrails(msg: str) -> list[str]:
    problems = []
    n = len(msg.split())
    if n > 40:
        problems.append(f"long ({n}w)")
    if "!" in msg:
        problems.append("exclamation")
    low = msg.lower()
    for b in BANNED:
        if b in low:
            problems.append(f"labels:'{b}'")
    return problems


def run():
    be = Backend()
    print(f"backend mode: {be.mode}\n" + "=" * 72)
    for name, events, expected in SCENARIOS:
        est = infer(events, now=T + 10)
        ok_state = "ok" if est.state is expected else f"WRONG (got {est.state.value})"
        prompt = build_prompt(est) if est.state is not State.NO_SIGNAL else None

        t0 = time.time()
        text = (be.complete(prompt) if prompt else None) or (
            FALLBACKS[est.support] if est.state is not State.NO_SIGNAL else "(silent)")
        dt = (time.time() - t0) * 1000

        issues = guardrails(text) if est.state is not State.NO_SIGNAL else []
        print(f"\n▶ {name}")
        print(f"   state:   {est.state.value}  [{ok_state}]  conf {est.confidence:.2f}")
        print(f"   latency: {dt:6.0f} ms")
        print(f"   guard:   {'clean' if not issues else ', '.join(issues)}")
        print(f"   message: {text}")
    print("\n" + "=" * 72)
    print("Latency + guardrails are automatic. Empathy/tone is a human call —")
    print("rate the messages above, then run again against the next model.")


if __name__ == "__main__":
    run()
