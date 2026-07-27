"""
study_log.py — the measurement layer for Darren's usability question:
"does delivering support THIS way actually yield perceived usefulness?"

We can only answer that if we log what happened. Every time the system decides
something (or deliberately stays silent) and every time a student responds, we
append one JSON line here. That gives us, per state:
  - how often it fired
  - how often the student engaged vs. ignored vs. dismissed  (our false-positive proxy)
  - what evidence drove it

Privacy: we log the STATE and EVIDENCE (which are already metadata — "same error
4x"), never source code, never raw keystrokes. One line per event, easy to load
into pandas for the writeup.
"""

from __future__ import annotations
import json, os, time
from typing import Optional

LOG_PATH = os.getenv("IDA_STUDY_LOG", os.path.join(os.path.dirname(__file__), "study_events.jsonl"))


def _write(record: dict):
    record["t"] = time.time()
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as e:      # logging must never break the student's session
        print(f"[study_log] could not write: {e}")


def log_decision(state: str, confidence: float, evidence: str,
                 support: str, shown: bool, session: Optional[str] = None):
    """Called on every /infer — including the silent ones (shown=False), because
    'chose to stay quiet' is itself data."""
    _write({"kind": "decision", "session": session, "state": state,
            "confidence": round(confidence, 3), "evidence": evidence,
            "support": support, "shown": shown})


def log_response(state: str, response: str, session: Optional[str] = None):
    """response in {'engaged','ignored','dismissed'} — how the student reacted."""
    _write({"kind": "response", "session": session,
            "state": state, "response": response})


# ------------------------------------------------------------------ analysis --
def summarize(path: Optional[str] = None) -> dict:
    """Quick per-state rollup for a standup or the paper. No pandas dependency.
    Returns {state: {shown, engaged, ignored, dismissed, dismissal_rate}}."""
    path = path or LOG_PATH
    if not os.path.exists(path):
        return {}
    return _rollup(path)


def _rollup(path: str) -> dict:
    states = {}
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            s = r.get("state", "?")
            st = states.setdefault(s, {"shown": 0, "engaged": 0, "ignored": 0, "dismissed": 0})
            if r["kind"] == "decision" and r.get("shown"):
                st["shown"] += 1
            elif r["kind"] == "response" and r["response"] in st:
                st[r["response"]] += 1
    for s, st in states.items():
        st["dismissal_rate"] = round(st["dismissed"] / st["shown"], 3) if st["shown"] else None
    return states


if __name__ == "__main__":
    # tiny self-test: log a few events to a temp file and roll them up
    import tempfile
    LOG_PATH = tempfile.mktemp(suffix=".jsonl")
    log_decision("stuck", 0.75, "same error 4x", "unblock", shown=True)
    log_response("stuck", "engaged")
    log_decision("stuck", 0.72, "same error 3x", "unblock", shown=True)
    log_response("stuck", "dismissed")
    log_decision("disengaged", 0.68, "away", "light_reengage", shown=False)
    from pprint import pprint
    pprint(_rollup(LOG_PATH))
