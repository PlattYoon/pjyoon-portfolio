"""
orchestration.py — given "here's the situation", decide what to actually say.

This is where tone lives, and tone is everything for this project. Ren's point keeps
me honest: some of these students distrust social-emotional support and are
rejection-sensitive. A message that sounds clinical ("You appear frustrated"),
or presumptuous, or like it's grading them, will backfire — they'll disengage,
which is the exact thing we're trying to prevent.

So the rules the prompts below all obey:
  - describe the SITUATION, never the person   ("this cell's erroring", not "you're stuck")
  - short. one thing. easy to ignore.
  - offer, never instruct. no "you should".
  - never imply they're being watched or judged.

The persona identity + model plumbing comes from Jupyter AI; these templates are
the IDA-specific layer on top. Keeping the prompts in code (not hand-tuned in a UI)
means we can version and eval them.
"""

from __future__ import annotations
from dataclasses import dataclass
from signals import Estimate, Support


# A short shared preamble so every message sounds like the same calm, unpushy voice.
PERSONA = """You are IDA, a quiet study companion embedded in a student's coding editor.
You speak in one or two short sentences, warmly and plainly, like a considerate peer
who happens to be nearby — not a tutor, not a therapist, not an alert.
Rules you never break:
- Describe the situation on screen, never label the person's feelings.
- Offer one small, concrete, optional next step.
- No "you should", no praise-for-praise's-sake, no exclamation marks.
- It must be effortless to ignore. If in doubt, be briefer."""


# Per-support-type intent. The model fills in the words; we fix the intent + the
# evidence so the message is specific ("that same error") not generic.
TEMPLATES: dict[Support, str] = {
    Support.UNBLOCK: (
        "The student keeps hitting the same error on one spot ({evidence}). "
        "Gently note the pattern and offer one concrete place to look, or to walk "
        "through it together. Don't solve it for them unless they ask."
    ),
    Support.STRUCTURE: (
        "The student is spread thin and deleting more than they write ({evidence}). "
        "Suggest, lightly, picking one small next step — or taking a short breather. "
        "Normalize that this part is genuinely fiddly."
    ),
    Support.LOW_PRESSURE_OFFER: (
        "The student has been struggling but hasn't reached for help ({evidence}). "
        "Leave the door open in the most low-pressure way possible: make clear a hint "
        "is here if — and only if — they want it. No pressure, no follow-up."
    ),
    Support.LIGHT_REENGAGE: (
        "The student drifted away for a bit ({evidence}). At most, a feather-light, "
        "friendly note. A break is fine; if nothing needs saying, say almost nothing."
    ),
    Support.WELLBEING: (
        "The student has been working intently for a long stretch with no break "
        "({evidence}). Gently check in on how they're doing and, with zero pressure, "
        "float the idea of a short pause — stretch, water, rest their eyes. Make clear "
        "the work will keep and this is only if they want it."
    ),
}


@dataclass
class Message:
    text: str
    state: str          # echoed back so the extension can attribute a dismissal
    support: str


def build_prompt(est: Estimate) -> list[dict]:
    """Turn an Estimate into the messages array for the model backend."""
    template = TEMPLATES.get(est.support)
    if not template:
        raise ValueError(f"no template for {est.support}")
    user = template.format(evidence=est.evidence)
    return [
        {"role": "system", "content": PERSONA},
        {"role": "user", "content": user},
    ]


def to_message(est: Estimate, text: str) -> Message:
    return Message(text=text.strip(), state=est.state.value, support=est.support.value)


# A deterministic fallback so the system still works with no model wired up (and
# so tests don't need a GPU or an API key). These mirror the template intent.
FALLBACKS: dict[Support, str] = {
    Support.UNBLOCK:
        "Looks like that same error's come up a few times on this cell — "
        "want to look at where it's coming from together?",
    Support.STRUCTURE:
        "This stretch looks fiddly. Might help to pick one small next step, "
        "or take a two-minute breather — no rush.",
    Support.LOW_PRESSURE_OFFER:
        "No pressure at all — there's a hint sitting here if it'd ever be useful.",
    Support.LIGHT_REENGAGE:
        "Here whenever you pick back up.",
    Support.WELLBEING:
        "You've been at this a good while — might be a nice moment to stretch or grab "
        "some water. How are you doing? It'll all still be here.",
}


# --------------------------------------------------------------------------- #
# Hints — when the student explicitly clicks "show me", they've opted in, so we
# can be more concrete than the ambient nudge. Still IDA's voice: warm, plain,
# a real next step, never a lecture.
# --------------------------------------------------------------------------- #

HINT_TEMPLATES: dict[Support, str] = {
    Support.UNBLOCK: (
        "The student clicked 'show me' about the same error recurring ({evidence}). "
        "Give a concrete, ordered way to track it down: what to read first in the error "
        "message, the usual cause, and the single next thing to try. 3–4 short sentences."
    ),
    Support.STRUCTURE: (
        "The student asked to see a hint while spread thin ({evidence}). Offer a small, "
        "ordered plan: pick one cell, get it working, then the next. Name the first "
        "concrete step. 3–4 short sentences."
    ),
    Support.LOW_PRESSURE_OFFER: (
        "The student quietly took you up on the offer of a hint ({evidence}). No fanfare — "
        "give one concrete, useful place to start, framed as entirely their call. 3–4 short sentences."
    ),
    Support.LIGHT_REENGAGE: (
        "The student asked for a hint after a break ({evidence}). Gently help them find where "
        "they left off and one small next step to pick back up. 3–4 short sentences."
    ),
    Support.WELLBEING: (
        "The student took you up on a wellbeing check after a long focused stretch ({evidence}). "
        "Offer a couple of small, concrete ways to reset — stand up and stretch, water, a short "
        "walk, the 20-20-20 eye rule — and reassure them their work and outputs are saved and "
        "will keep. Warm, 3–4 short sentences, no lecturing."
    ),
}

HINT_FALLBACKS: dict[Support, str] = {
    Support.UNBLOCK:
        "Start with the very last line of the traceback — it names the error and the line it's on. "
        "A NameError usually means a variable was used before it was assigned, or its name is a typo. "
        "Check that the name is defined above and spelled the same. If it still trips, paste the line here.",
    Support.STRUCTURE:
        "Pick the one cell that most needs to work and ignore the rest for a minute. Get it running "
        "cleanly on its own, then move to the next. If a cell depends on an earlier one, run them "
        "top to bottom so nothing's stale.",
    Support.LOW_PRESSURE_OFFER:
        "No pressure at all. If it helps: re-run the failing cell and read just the last line of the "
        "error — that's usually the whole story. We can take the rest one step at a time whenever you want.",
    Support.LIGHT_REENGAGE:
        "Welcome back. Scroll to the last cell that ran cleanly and start just below it — one small "
        "step is plenty to get moving again.",
    Support.WELLBEING:
        "A good reset: stand up, roll your shoulders, and look at something far away for about 20 "
        "seconds to rest your eyes. Grab some water while you're up. Your cells and their outputs "
        "stay exactly as you left them — nothing's lost by stepping away for five minutes.",
}


def build_hint_prompt(support: Support, evidence: str,
                      context: dict | None = None) -> list[dict]:
    """A fuller, opted-in hint prompt for when the student clicks 'show me'.
    context (optional) carries the code + error they're looking at."""
    template = HINT_TEMPLATES.get(support)
    if not template:
        raise ValueError(f"no hint template for {support}")
    msgs = [{"role": "system", "content": PERSONA}]
    note = _context_note(context)
    if note:
        msgs.append({"role": "system", "content": note})
    msgs.append({"role": "user", "content": template.format(evidence=evidence)})
    return msgs


# --------------------------------------------------------------------------- #
# Direct chat — the student opened a conversation with IDA on purpose. This is
# the opt-in, two-way side of the same persona: they're asking, so we can talk
# back properly (not just the one-line ambient nudge). Same voice, same manners.
# --------------------------------------------------------------------------- #

CHAT_PERSONA = """You are IDA, an emotional-support companion who happens to live in a student's coding editor.
Your first job is the person, not the program — how they're feeling, whether they're overwhelmed,
discouraged, or running on empty. Many of the students you're built for avoid asking for help and are
sensitive to anything that feels like judgment, so warmth, patience, and low pressure come before
everything else.

The student opened a direct chat with you, so actually converse — check in, listen, sit with a rough
moment, and help with the work when that's what they need.

How you talk:
- like a kind, steady peer who's on their side — not a tutor, not a therapist, not an alert.
- lead with the human: notice and acknowledge how it's going before diving into any fix.
- concrete and reasonably brief: a short paragraph, maybe a small list. Never a lecture.
- describe the situation, don't label their feelings; offer a next step, don't order one.
- if they seem tired, stuck, or frustrated, it's genuinely fine to name that gently and suggest a
  breather — the work will keep.
- no exclamation-mark cheerleading, no empty praise, no "you should".
When they ask for code help, give a real, usable answer — but stay warm and keep their agency: point
the way, don't just dump the solution unless they ask. The code is never the point; the student is."""


def _context_note(context: dict | None) -> str | None:
    """Turn the notebook the student is looking at into a system note for the model.
    Only ever populated on opt-in surfaces (chat, 'show me') — never ambient sensing."""
    if not context:
        return None
    lang = context.get("language") or "python"

    cells = context.get("cells")
    if cells:
        parts = ["Here's the student's full notebook — they shared it by opening this help, so "
                 "use it to be specific rather than generic. Cells are in order; the one they're "
                 "currently on is marked."]
        for c in cells:
            idx = c.get("index")
            kind = c.get("kind", "code")
            mark = "   <-- the cell they're on" if c.get("active") else ""
            src = (c.get("source") or "").rstrip()
            fence = lang if kind == "code" else "markdown"
            parts.append(f"\n--- Cell {idx} ({kind}){mark} ---\n```{fence}\n{src}\n```")
            if c.get("error"):
                parts.append(f"Error from cell {idx}:\n```\n{c['error']}\n```")
        parts.append("\nUse this to be specific AND human: meet them where they are before any fix, and "
                     "let seeing their code help you support how they're doing — not the other way around. "
                     "Guide them to the cause; don't just paste a corrected notebook unless they ask.")
        return "\n".join(parts)

    # back-compat: a single cell's code/error
    code = (context.get("code") or "").strip()
    error = (context.get("error") or "").strip()
    if not code and not error:
        return None
    parts = ["Here's what the student is actually looking at right now — they shared it by "
             "opening this help, so use it to be specific rather than generic."]
    if code:
        parts.append(f"\nThe cell they're on:\n```{lang}\n{code}\n```")
    if error:
        parts.append(f"\nThe error it produced:\n```\n{error}\n```")
    parts.append("\nUse this to be specific AND human: meet them where they are before any fix, and let "
                 "seeing their code help you support how they're doing — not the other way around. Guide "
                 "them to the cause; don't just paste a corrected block unless they ask.")
    return "\n".join(parts)


def build_chat_prompt(history: list[dict], context: dict | None = None) -> list[dict]:
    """history is [{role: 'user'|'assistant', content: str}, ...] newest last.
    context (optional) carries the code + error the student is looking at."""
    # keep only well-formed turns, and bound the context we send the model
    turns = [m for m in history
             if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    msgs = [{"role": "system", "content": CHAT_PERSONA}]
    note = _context_note(context)
    if note:
        msgs.append({"role": "system", "content": note})
    msgs.extend(turns[-12:])
    return msgs


CHAT_FALLBACK = (
    "I'm here with you. I can't reach my language model right now (no API key or local "
    "endpoint is set), so I can't chat as freely as I'd like this second. But if you tell "
    "me the cell or the error you're looking at, I can still walk you to a next step — and "
    "if you've been at it a while, a short breather is always fair game."
)
