# IDA — Behavioral signals (read `service/signals.py`)

The taxonomy *is* `service/signals.py` — it's a runnable spec. Run `python signals.py` and the
scenario tests print exactly what each situation maps to. This page is just the why.

**The framing that matters:** we are not detecting emotions. We're detecting *support
opportunities* — "this looks like a moment a small optional offer of help might land." Nothing
stronger. Everything is built to be easy to ignore, because (a) it's wrong a lot, and (b) our
users avoid help out of rejection sensitivity, so a pushy or presumptuous message is the exact
thing that makes them disengage.

## The pipeline (three layers, on purpose)

```
events            →   features (windowed)        →   state
(from editor)         (interpretable, logged)        (a support opportunity)

cell_run{error}       error_rerun_streak             stuck        → unblock
idle{focused}         idle_ratio                     overwhelmed  → structure
edit_churn            churn_without_progress         disengaged   → (usually nothing)
file_switch           spread                         withdrawn    → low-pressure offer
task_abandon          help_avoidance                 no_signal    → silence  ← most of the time
```

We keep the middle **features** layer readable instead of mapping raw events straight to states
with a black box — it's what lets a message say *"same error a few times"* instead of guessing,
and it's what we log to debug false positives.

## The states (all defined in code as `State` + `classify()`)

| State | The pattern | We offer | How careful |
|-------|-------------|----------|-------------|
| `stuck` | circling one error, one spot | a concrete unblock / hint | low |
| `overwhelmed` | deleting > writing across several places | break it down / a breather | medium |
| `disengaged` | away, drifting | usually **nothing** — a break isn't a problem | high |
| `withdrawn` | struggling **and** never opening help, then leaving | gentlest optional offer | highest |
| `no_signal` | below threshold / recovering | stay quiet | — |

`withdrawn` is the one the project exists for — the student who won't ask. It's also the easiest
to get wrong, so it has the strictest floor.

## The manners (also in code, not an afterthought)

These are enforced in `infer()` / `classify()` / `DismissalMemory`:

- **no single-feature triggers** — a state needs a *combination* clearing a confidence floor
- **every estimate carries its evidence** — so messages are specific and false positives debuggable
- **restraint scales with ambiguity** — `disengaged`/`withdrawn` floors are highest
- **silence is the default and preferred output**
- **dismissal is memory** — wave off a type twice and we stop offering it
- **describe the situation, never the person** — "this cell's erroring", not "you seem anxious"

## Privacy / consent (before we instrument anything)

`signals.py` works on **metadata** (run/error/idle/churn shapes), not source text or literal
keystrokes. That's deliberate — we can build and study *now* without special data collection.
Anything keystroke-dynamics or camera/mouth-movement (Michael's dataset work) is a categorically
higher consent tier: IRB-approved, opt-in, and best paired with **local model mode** so nothing
leaves the machine.

## How Michael's work plugs in

His richer signals become **new feature rows** feeding the same layer — new entries in the event
table and `Features`, no change to the states or rules. The taxonomy was built to absorb better
inputs later without rewriting.
