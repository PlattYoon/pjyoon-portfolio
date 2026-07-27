"""
signals.py — turn what a student *does* in the editor into a guess about what
kind of support (if any) might help right now.

This is the heart of the project. A few things I want to be honest about up front,
because they shaped every line below:

  - We are NOT detecting emotions. We're detecting *support opportunities*. The
    output is "this looks like a moment where a small, optional offer of help might
    land well" — nothing stronger. Claiming to know how someone feels from their
    keystrokes would be both wrong and a little insulting.
  - This is wrong a lot. False positives are the default, not the exception. So the
    whole thing is built to be easy to ignore: silence is the most common output,
    no single signal ever fires a message, and if a student waves us off we back off.
  - Our users avoid help out of rejection sensitivity. A pushy or presumptuous
    message is exactly what makes them close the tab. Restraint is a feature.

Pipeline (see ARCHITECTURE.md):  events -> features (windowed) -> state estimate.

Everything here is pure and testable. The VS Code extension feeds it events; the
server hands the resulting state to the persona layer to actually word the message.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# --------------------------------------------------------------------------- #
# Events — what the editor sends us. Metadata only, no source code by default.
# The `type` strings here MUST match what src/extension.ts emits.
# --------------------------------------------------------------------------- #

@dataclass
class Event:
    t: float                      # unix seconds
    type: str                     # "cell_run" | "idle" | "edit_churn" | ...
    data: dict = field(default_factory=dict)


# convenience constructors so traces read like English (used in tests below)
def cell_run(t, status, error_type=None, cell_id=None, consecutive_failures=0):
    return Event(t, "cell_run", {"status": status, "error_type": error_type,
                                 "cell_id": cell_id,
                                 "consecutive_failures": consecutive_failures})

def idle(t, duration_ms, focused=True):
    return Event(t, "idle", {"duration_ms": duration_ms, "focused": focused})

def edit_churn(t, inserted, deleted, window_ms=8000):
    return Event(t, "edit_churn", {"inserted": inserted, "deleted": deleted,
                                   "window_ms": window_ms})

def file_switch(t, to, dwell_ms):
    return Event(t, "file_switch", {"to": to, "dwell_ms": dwell_ms})

def help_opened(t):
    return Event(t, "help_opened", {})

def task_abandon(t, task_id):
    return Event(t, "task_marker", {"marker": "abandoned", "task_id": task_id})

def frustration_signal(t, score, source="keystroke"):
    # An EXTERNAL signal — e.g. Michael's keystroke-dynamics / mouth-movement model
    # emitting a 0..1 frustration score. It arrives on the same event stream and
    # becomes just another feature (see extract_features). By design it never fires
    # a message on its own; it only reinforces a behavioral state we already see.
    return Event(t, "frustration_signal", {"score": float(score), "source": source})

def wellbeing_pulse(t, continuous_min):
    # A heartbeat from the editor: how many minutes the student has been working
    # more-or-less continuously, with no real break. The extension resets this to 0
    # whenever it sees a genuine break. It's what lets IDA notice a marathon session
    # and suggest a pause — the wellbeing side of support, not the "you're stuck" side.
    return Event(t, "wellbeing_pulse", {"continuous_min": float(continuous_min)})


# --------------------------------------------------------------------------- #
# States + support types — the vocabulary the rest of the system speaks.
# --------------------------------------------------------------------------- #

class State(str, Enum):
    STUCK = "stuck"                # a concrete blocker, going in circles on one thing
    OVERWHELMED = "overwhelmed"    # thrashing broadly, lost the thread
    DISENGAGED = "disengaged"      # drifted off — but this might just be a break
    WITHDRAWN = "withdrawn"        # struggling AND avoiding help (the pattern we care most about)
    LONG_SESSION = "long_session"  # heads-down a long time with no break — a wellbeing moment
    NO_SIGNAL = "no_signal"        # the correct answer most of the time


class Support(str, Enum):
    UNBLOCK = "unblock"                    # name the blocker, offer one next step
    STRUCTURE = "structure"                # break it down / normalize / suggest a pause
    LIGHT_REENGAGE = "light_reengage"      # a feather-light nudge, or nothing
    LOW_PRESSURE_OFFER = "low_pressure_offer"  # gentlest possible, fully optional
    WELLBEING = "wellbeing"                # check in, suggest a break — care, not correction
    NONE = "none"


# Wellbeing thresholds (minutes of continuous work with no break). Two tiers:
# past STRONG we'll gently interrupt even a real problem (an hour nonstop matters);
# past MODERATE we only suggest a break when nothing else needs saying.
WELLBEING_STRONG_MIN = 60.0
WELLBEING_MODERATE_MIN = 40.0


# How much evidence we demand before acting, per state. More ambiguous ==
# more restraint. `disengaged` and `withdrawn` are deliberately hard to trigger.
CONFIDENCE_FLOOR = {
    State.STUCK: 0.60,
    State.OVERWHELMED: 0.65,
    State.DISENGAGED: 0.80,
    State.WITHDRAWN: 0.78,
    State.LONG_SESSION: 0.70,
}


# --------------------------------------------------------------------------- #
# Features — the interpretable middle layer. Each is a small, named signal
# computed over a rolling window. We keep this layer human-readable on purpose:
# it's what lets a message say "same error a few times" instead of guessing,
# and it's what we log to debug false positives later.
# --------------------------------------------------------------------------- #

@dataclass
class Features:
    error_rerun_streak: int = 0        # same error, re-run, barely edited between
    thrash_index: float = 0.0          # lots of edits+runs, nothing resolving
    churn_without_progress: float = 0.0  # deleted >> inserted
    idle_ratio: float = 0.0            # focused-but-idle time / window (staring, not away)
    away_ratio: float = 0.0            # window unfocused / window
    task_abandoned: bool = False
    help_avoidance: bool = False       # errors persist, help never opened
    spread: int = 0                    # how many distinct cells/files are churning
    external_frustration: float = 0.0  # 0..1 from an external model (e.g. Michael's)
    continuous_active_min: float = 0.0 # minutes worked without a real break (wellbeing)

    def any(self) -> bool:
        return (self.error_rerun_streak or self.thrash_index or
                self.churn_without_progress or self.idle_ratio or
                self.away_ratio or self.task_abandoned or
                self.external_frustration or self.continuous_active_min)


def extract_features(events: list[Event], window_s: float = 240.0,
                     now: Optional[float] = None) -> Features:
    """Fold recent events into features. Coarse by design — we'd rather miss a
    real moment than invent one."""
    now = now if now is not None else time.time()
    recent = [e for e in events if now - e.t <= window_s]
    f = Features()
    if not recent:
        return f

    total = max(1e-6, window_s)
    idle_focused_ms = sum(e.data["duration_ms"] for e in recent
                          if e.type == "idle" and e.data.get("focused"))
    away_ms = sum(e.data["duration_ms"] for e in recent
                  if e.type == "idle" and not e.data.get("focused"))
    f.idle_ratio = min(1.0, idle_focused_ms / 1000 / total)
    f.away_ratio = min(1.0, away_ms / 1000 / total)

    runs = [e for e in recent if e.type == "cell_run"]
    errors = [e for e in runs if e.data.get("status") == "error"]
    f.error_rerun_streak = max((e.data.get("consecutive_failures", 0)
                                for e in errors), default=0)

    inserted = sum(e.data["inserted"] for e in recent if e.type == "edit_churn")
    deleted = sum(e.data["deleted"] for e in recent if e.type == "edit_churn")
    if inserted + deleted > 0:
        f.churn_without_progress = deleted / (inserted + deleted)

    # thrash = busy hands, no forward motion: many runs, most failing, lots of churn
    if runs:
        fail_rate = len(errors) / len(runs)
        f.thrash_index = round(fail_rate * min(1.0, (inserted + deleted) / 400.0), 3)

    # spread = how many distinct cells are actually FAILING. Deliberately NOT
    # counting passive file navigation (settings, the IDA panel, another tab):
    # glancing around isn't thrashing, and counting it used to mask a real,
    # single-cell 'stuck' — the classifier would go quiet mid-struggle.
    cells = {e.data.get("cell_id") for e in errors if e.data.get("cell_id")}
    f.spread = len(cells)

    f.task_abandoned = any(e.type == "task_marker"
                           and e.data.get("marker") == "abandoned" for e in recent)
    # help_avoidance: we saw errors, we never saw help get opened
    f.help_avoidance = bool(errors) and not any(e.type == "help_opened" for e in recent)

    # external frustration (Michael's model): take the strongest recent reading.
    # Just another feature — the classifier decides what to do with it, if anything.
    fr = [e.data.get("score", 0.0) for e in recent if e.type == "frustration_signal"]
    f.external_frustration = max(fr) if fr else 0.0

    # wellbeing heartbeat from the editor: how long they've been heads-down without
    # a break. Take the latest reading (the extension already resets it on a break).
    pulses = [e for e in recent if e.type == "wellbeing_pulse"]
    if pulses:
        latest = max(pulses, key=lambda e: e.t)
        f.continuous_active_min = float(latest.data.get("continuous_min", 0.0))
    return f


# --------------------------------------------------------------------------- #
# Classifier — features -> a state estimate, with the evidence that produced it.
# Rule-based on purpose: transparent, debuggable, and the rules ARE the taxonomy.
# --------------------------------------------------------------------------- #

@dataclass
class Estimate:
    state: State
    confidence: float
    evidence: str                  # human-readable "why", passed to the message layer
    support: Support

    @property
    def actionable(self) -> bool:
        floor = CONFIDENCE_FLOOR.get(self.state, 1.1)
        return self.state is not State.NO_SIGNAL and self.confidence >= floor


_SILENT = Estimate(State.NO_SIGNAL, 0.0, "nothing worth interrupting for", Support.NONE)


def classify(f: Features) -> Estimate:
    """Pick at most one state. Ordering matters: we check the states that most
    warrant a gentle touch (withdrawn) before the safer ones, but each still has
    to clear its own confidence floor in `actionable`."""

    # An external frustration reading (Michael's model) never fires a message by
    # itself — but when we ALREADY see a struggle behaviorally, a high reading makes
    # us a little more confident and a little more specific. Reinforcement, not trigger.
    hot = f.external_frustration >= 0.6
    boost = 0.12 if hot else 0.0
    tag = "  · corroborated by frustration signal" if hot else ""

    # wellbeing (strong): an hour-plus heads-down with no break is worth a gentle
    # check-in even mid-problem — a tired brain circling an error rarely breaks it.
    # This is the one case where care outranks the "let me solve it" instinct.
    if f.continuous_active_min >= WELLBEING_STRONG_MIN:
        conf = 0.70 + min(0.25, 0.01 * (f.continuous_active_min - WELLBEING_STRONG_MIN))
        return Estimate(State.LONG_SESSION, min(conf, 0.95),
                        f"heads-down for about {int(f.continuous_active_min)} minutes without a break",
                        Support.WELLBEING)

    # withdrawn: struggling AND actively not reaching for help, then bailing.
    # this is the whole reason the project exists, so we look for it first —
    # but it's also the easiest to get wrong, so its floor is high.
    if f.help_avoidance and (f.task_abandoned or f.error_rerun_streak >= 2):
        conf = 0.6 + 0.1 * f.error_rerun_streak + (0.15 if f.task_abandoned else 0) + boost
        return Estimate(State.WITHDRAWN, min(conf, 0.95),
                        "kept hitting errors without opening help, then stepped away" + tag,
                        Support.LOW_PRESSURE_OFFER)

    # stuck: circling one concrete blocker.
    if f.error_rerun_streak >= 3 and f.spread <= 1:
        conf = 0.55 + 0.1 * (f.error_rerun_streak - 2) + 0.15 * f.thrash_index + boost
        return Estimate(State.STUCK, min(conf, 0.95),
                        f"same error {f.error_rerun_streak}x on one cell" + tag,
                        Support.UNBLOCK)

    # overwhelmed: thrashing across several places, deleting more than writing.
    if f.spread >= 2 and (f.churn_without_progress > 0.6 or f.idle_ratio > 0.4):
        conf = 0.55 + 0.2 * f.churn_without_progress + 0.15 * min(1.0, f.spread / 3) + boost
        return Estimate(State.OVERWHELMED, min(conf, 0.95),
                        "lots of deleting and re-running across a few places, not much landing" + tag,
                        Support.STRUCTURE)

    # wellbeing (moderate): a long focused stretch, but they're not visibly
    # struggling right now — so we only suggest a breather, and only once it's
    # gone on a while. Reached only if nothing more urgent matched above.
    if f.continuous_active_min >= WELLBEING_MODERATE_MIN:
        conf = 0.65 + 0.01 * (f.continuous_active_min - WELLBEING_MODERATE_MIN)
        return Estimate(State.LONG_SESSION, min(conf, 0.90),
                        f"focused for about {int(f.continuous_active_min)} minutes straight",
                        Support.WELLBEING)

    # disengaged: mostly away / drifting. lowest confidence, highest chance it's
    # just a well-earned break — so we lean toward saying nothing.
    if f.away_ratio > 0.6 and not f.error_rerun_streak:
        return Estimate(State.DISENGAGED, 0.5 + 0.3 * (f.away_ratio - 0.6) / 0.4,
                        "away from the editor for a while", Support.LIGHT_REENGAGE)

    return _SILENT


# --------------------------------------------------------------------------- #
# The one public entrypoint the server calls. Wraps classify with the
# harm-reduction rules that aren't really "logic" so much as "manners".
# --------------------------------------------------------------------------- #

class DismissalMemory:
    """If a student waves off a kind of message, we stop offering it. Simple,
    but it's the difference between 'ambient' and 'nagging'."""
    def __init__(self, hard_stop_after: int = 2):
        self._counts: dict[State, int] = {}
        self._hard_stop = hard_stop_after

    def record_dismissal(self, state: State):
        self._counts[state] = self._counts.get(state, 0) + 1

    def suppressed(self, state: State) -> bool:
        return self._counts.get(state, 0) >= self._hard_stop

    def penalty(self, state: State) -> float:
        # each dismissal makes us want more evidence next time
        return 0.1 * self._counts.get(state, 0)


def infer(events: list[Event],
          memory: Optional[DismissalMemory] = None,
          now: Optional[float] = None) -> Estimate:
    """events in -> a support opportunity out (usually NO_SIGNAL). This is the
    whole taxonomy behind one call."""
    f = extract_features(events, now=now)
    if not f.any():
        return _SILENT

    est = classify(f)
    if est.state is State.NO_SIGNAL:
        return est

    if memory:
        if memory.suppressed(est.state):
            return _SILENT                      # they've told us twice; stop.
        est.confidence -= memory.penalty(est.state)

    # never act on a hunch
    return est if est.actionable else _SILENT


# --------------------------------------------------------------------------- #
# Scenario tests — these double as the spec. Run: python signals.py
# Each trace is a little story; the assertion is what we think should happen.
# --------------------------------------------------------------------------- #

def _run_scenarios():
    t = 1_000_000.0

    # 1. Circling one error -> stuck, offer to unblock.
    stuck = [cell_run(t + i, "error", "NameError", "c3", consecutive_failures=i + 1)
             for i in range(4)] + [help_opened(t + 5)]
    e = infer(stuck, now=t + 6)
    assert e.state is State.STUCK and e.actionable, e
    print(f"[stuck]       {e.confidence:.2f}  «{e.evidence}» -> {e.support.value}")

    # 2. Deleting more than writing, across a few cells -> overwhelmed.
    ov = [edit_churn(t, inserted=10, deleted=200),
          edit_churn(t + 5, inserted=5, deleted=150),
          cell_run(t + 6, "error", "ValueError", "a"),
          cell_run(t + 7, "error", "KeyError", "b"),
          file_switch(t + 8, "other.ipynb", dwell_ms=3000),
          help_opened(t + 9)]
    e = infer(ov, now=t + 10)
    assert e.state is State.OVERWHELMED and e.actionable, e
    print(f"[overwhelmed] {e.confidence:.2f}  «{e.evidence}» -> {e.support.value}")

    # 3. Struggling and never opening help, then leaving -> withdrawn.
    wd = [cell_run(t, "error", "TypeError", "z", consecutive_failures=1),
          cell_run(t + 4, "error", "TypeError", "z", consecutive_failures=2),
          task_abandon(t + 8, "assignment-2")]
    e = infer(wd, now=t + 9)
    assert e.state is State.WITHDRAWN and e.actionable, e
    print(f"[withdrawn]   {e.confidence:.2f}  «{e.evidence}» -> {e.support.value}")

    # 4. Just... away. Probably a break. We DO recognize it as disengaged, but the
    # confidence floor is high on purpose, so infer() stays quiet. Detected != acted on.
    away = [idle(t, duration_ms=200_000, focused=False)]
    raw = classify(extract_features(away, now=t + 210))
    assert raw.state is State.DISENGAGED and not raw.actionable, raw
    assert infer(away, now=t + 210).state is State.NO_SIGNAL
    print(f"[disengaged]  saw it ({raw.confidence:.2f} < floor) but held back — "
          f"a break isn't a problem to fix ✔")

    # 5. Quiet, healthy work -> NO_SIGNAL. The common case.
    calm = [cell_run(t, "ok", cell_id="c1"), cell_run(t + 30, "ok", cell_id="c2")]
    e = infer(calm, now=t + 40)
    assert e.state is State.NO_SIGNAL, e
    print(f"[silence]     stayed quiet ✔")

    # 6. Dismissal memory: after two brush-offs, stop offering that type.
    mem = DismissalMemory(hard_stop_after=2)
    mem.record_dismissal(State.STUCK); mem.record_dismissal(State.STUCK)
    e = infer(stuck, memory=mem, now=t + 6)
    assert e.state is State.NO_SIGNAL, e
    print(f"[dismissed]   respected the brush-off ✔")

    # 7. Michael's frustration signal: on its own it does NOTHING (no behavior to
    # reinforce); paired with a real struggle it raises confidence + specificity.
    just_frustration = [frustration_signal(t, 0.9)]
    assert infer(just_frustration, now=t + 1).state is State.NO_SIGNAL
    plain = infer(stuck, now=t + 6)
    boosted = infer(stuck + [frustration_signal(t + 4, 0.9)], now=t + 6)
    assert boosted.state is State.STUCK and boosted.confidence > plain.confidence
    print(f"[external]    alone: silent ✔   with struggle: {plain.confidence:.2f} -> "
          f"{boosted.confidence:.2f}, «{boosted.evidence}» ✔")

    # 8. Wellbeing: a long heads-down stretch with no break -> a gentle break offer.
    #    A short session stays quiet; a marathon outranks even an active struggle.
    marathon = [wellbeing_pulse(t, continuous_min=68)]
    e = infer(marathon, now=t + 1)
    assert e.state is State.LONG_SESSION and e.support is Support.WELLBEING and e.actionable, e
    print(f"[wellbeing]   {e.confidence:.2f}  «{e.evidence}» -> {e.support.value}")

    assert infer([wellbeing_pulse(t, continuous_min=12)], now=t + 1).state is State.NO_SIGNAL
    both = stuck + [wellbeing_pulse(t + 4, continuous_min=72)]
    assert infer(both, now=t + 6).support is Support.WELLBEING     # care outranks 'stuck' after an hour
    print(f"[wellbeing]   short session stayed quiet ✔   outranked an active struggle at 72m ✔")

    print("\nall scenarios passed.")


if __name__ == "__main__":
    _run_scenarios()
