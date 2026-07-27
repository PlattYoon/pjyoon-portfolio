"""
server.py — the seam between the editor and the brains.

The VS Code extension posts a buffer of events here every ~30s; we run it through
the taxonomy (signals.py), and IF something's worth saying, word it (orchestration.py
+ backend.py) and hand back a single message. Most of the time we hand back nothing,
which is the point.

Endpoints:
    POST /infer    {events:[...]} -> {} | {message, state, support}
    POST /dismiss  {state}        -> {}   (student waved off this kind of message)

Run:  python server.py     (stdlib only; no framework needed for a prototype)
"""

from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def _load_dotenv() -> None:
    """Load .env into the environment so a key dropped there 'just works', no matter
    who launched us. The VS Code extension spawns this process with a bare env and
    nothing sources .env for it — so we do it ourselves. Zero dependencies; existing
    real env vars always win over the file."""
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, ".env"), os.path.join(os.path.dirname(here), ".env")):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if val[:1] in ("'", '"'):                 # quoted: take what's inside
                    quote = val[0]
                    val = val[1:].split(quote, 1)[0]
                else:                                     # unquoted: drop inline comment
                    hashpos = val.find("#")
                    if hashpos == 0:                      # value is only a comment -> empty
                        val = ""
                    elif hashpos > 0 and val[hashpos - 1] in " \t":
                        val = val[:hashpos].rstrip()
                if key and val and key not in os.environ:
                    os.environ[key] = val


_load_dotenv()

from signals import Event, DismissalMemory, infer, State, Support
from orchestration import (build_prompt, to_message, FALLBACKS,
                           build_hint_prompt, HINT_FALLBACKS,
                           build_chat_prompt, CHAT_FALLBACK)
from backend import Backend
import study_log

PORT = 8770
_backend = Backend()
_memory = DismissalMemory()   # persists for the session; swap for per-user store later


def decide(raw_events: list[dict]) -> dict:
    """events -> a message, or {} for silence."""
    events = [Event(e["t"], e["type"], e.get("data", {})) for e in raw_events]
    est = infer(events, memory=_memory)
    if est.state is State.NO_SIGNAL:
        study_log.log_decision("no_signal", est.confidence, est.evidence,
                               est.support.value, shown=False)  # silence is data too
        return {}   # the usual answer

    prompt = build_prompt(est)
    text = _backend.complete(prompt) or FALLBACKS[est.support]  # graceful if no model
    msg = to_message(est, text)
    study_log.log_decision(msg.state, est.confidence, est.evidence, msg.support, shown=True)
    return {"message": msg.text, "state": msg.state, "support": msg.support,
            "evidence": est.evidence}


def make_hint(support_val: str, evidence: str, context: dict | None = None) -> dict:
    """The student clicked 'show me' — hand back a fuller, opted-in hint."""
    try:
        support = Support(support_val)
    except ValueError:
        support = Support.NONE
    if support is Support.NONE:
        return {"hint": "Tell me which cell or error you're looking at and "
                        "we'll take it one step at a time."}
    text = _backend.complete(build_hint_prompt(support, evidence, context)) \
        or HINT_FALLBACKS.get(support, "")
    return {"hint": text}


def make_chat(history: list[dict], context: dict | None = None) -> dict:
    """The student is talking to IDA directly — converse back, in persona."""
    if not history:
        return {"reply": "Hey — I'm here. What's on your mind?"}
    reply = _backend.complete(build_chat_prompt(history, context), max_tokens=320) or CHAT_FALLBACK
    study_log.log_response("chat", "engaged")   # a direct chat is engagement, by definition
    return {"reply": reply.strip()}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or "{}")

        if self.path == "/infer":
            self._json(200, decide(body.get("events", [])))
        elif self.path == "/dismiss":
            state = body.get("state")
            if state:
                _memory.record_dismissal(State(state))
                study_log.log_response(state, "dismissed")
            self._json(200, {})
        elif self.path == "/respond":
            # extension reports engagement: {state, response in engaged|ignored}
            if body.get("state"):
                study_log.log_response(body["state"], body.get("response", "engaged"))
            self._json(200, {})
        elif self.path == "/hint":
            # student clicked "show me" -> a fuller, opted-in hint
            self._json(200, make_hint(body.get("support", ""), body.get("evidence", ""),
                                      body.get("context")))
        elif self.path == "/chat":
            # student opened a direct conversation with IDA
            self._json(200, make_chat(body.get("messages", []), body.get("context")))
        else:
            self._json(404, {"error": "unknown endpoint"})

    def log_message(self, *_):  # quiet console
        pass


if __name__ == "__main__":
    print(f"IDA service on :{PORT}  (model backend: {_backend.mode})")
    # bind IPv4 explicitly: the VS Code extension hits 127.0.0.1, and "localhost"
    # can otherwise resolve to IPv6 (::1) and never meet it.
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
