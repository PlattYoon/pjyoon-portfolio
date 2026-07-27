# IDA — Weekly Summary

**Platt Yoon · week of Jul 13–20, 2026 · VariAbility Lab (Pathways for AI)**

This connects what I built this week to what the team discussed in the Jul 6-era stand-up
(Darren, Michael, Adrian, Tammy, Isabella), so the pieces line up rather than drift apart.

---

## 1. What I built this week

I stood up the `jupyter-ai-vscode` component end to end — not as prose specs but as running
code — covering the two things I'd taken on: the **system architecture** and the
**behavioral-signal → social-emotional inference layer**. The whole loop runs today, even with
no API key (it falls back to canned support lines), so it's demoable now.

The path, and where each piece lives:

| Stage | What it does | File |
|-------|--------------|------|
| Capture | watches edits, errors, idle, focus, file switches — metadata only, no source text | `src/extension.ts` |
| Inference | events → features → a support state + confidence + evidence | `service/signals.py` |
| Orchestration | state → prompt; persona voice + per-support templates (tone lives here) | `service/orchestration.py` |
| Backend | one interface over local (Qwen3/Llama via vLLM) and API (Claude/GPT) | `service/backend.py` |
| Delivery | proactive, inline, rate-limited, dismissible message | `src/extension.ts` + `service/server.py` |

**The inference layer** is the research core. It maps ordinary editor behavior to four support
states plus a silence default:

- `stuck` — circling one error in one spot → offer a concrete unblock
- `overwhelmed` — deleting more than writing across several places → suggest structure / a breather
- `disengaged` — away, drifting → usually **nothing** (a break isn't a problem)
- `withdrawn` — struggling **and** never opening help, then leaving → gentlest optional offer
- `no_signal` — the most common output, by design

The framing throughout: **we detect support *opportunities*, not emotions.** Messages describe
the situation ("this cell has errored a few times"), never the person ("you seem anxious"). The
caution is built in — no single signal triggers a message, the most ambiguous states have the
strictest confidence floors, and it stops offering a message type once a student waves it off.
Scenario tests cover each case and pass (`python service/signals.py`).

**The architecture's load-bearing idea:** Jupyter AI is request/response — the student asks, it
answers. IDA needs the inverse: notice something and speak first. There's no upstream
documentation for proactive messaging, so I isolated that unsolved piece into a small custom
delivery layer and kept everything else on supported APIs.

---

## 2. How this lines up with last week's meeting

The stand-up made it clear the technical work is converging from three directions. Mapping
those to what I built:

**Adrian — persona extension + inline redirect.** Adrian said that now his class assignment is
done, between now and Thursday he'll extend the default Jupyter AI persona and make inline error
messages redirect the student into our chat interface. Rather than have us both build this, I
went ahead and implemented the native persona side: `personas/` now holds four real Jupyter AI
`BasePersona` subclasses — `@IDA-Unblock`, `@IDA-Focus`, `@IDA-Nearby`, `@IDA-Checkin` — one per
support mode, registered via entry points so they're @-mentionable in the Jupyter AI chat. These
are the *on-demand* side; the proactive delivery service reuses the same four voices. One thing
worth knowing that shaped this: in Jupyter AI v3 every persona (even Jupyternaut) only replies
when @-mentioned, so the proactive behavior genuinely can't live inside a persona — hence the
split. **Action: still worth showing Adrian, so he builds on these rather than a parallel set.**

**Michael — context awareness + frustration datasets.** Michael improved response speed (≈1 min
→ 10–15s) by letting the agent use Jupyter AI's file-manager tool instead of scraping files on
every message, and he found existing keystroke-dynamics and mouth-movement datasets to bootstrap
frustration detection without collecting raw user data first. Both fit cleanly:
- His **active-file ambiguity blocker** ("debug my code" with no file specified) is the same
  problem my capture layer handles via `onDidChangeActiveTextEditor` with a most-recently-focused
  fallback — worth comparing notes.
- His **datasets** slot into my inference layer as *new feature inputs*: they'd become new rows
  in the event/feature tables feeding the same `classify()`, no change to the states or rules. So
  his frustration signal and my behavioral states compose rather than compete. **Action: agree
  with Michael on how "frustration" from those datasets maps onto the feature layer; grab the
  dataset from Discord.**

**Darren — ATI / usability framing.** Darren framed the contribution around whether implementing
awareness *this way* yields perceived usefulness of the support — a future usability study. My
design supports that: confidence thresholds and cooldown are deliberately exposed as tunable
parameters, and every message carries its evidence, so we can log (state, evidence, message,
response) and measure it. That logging is the natural bridge into the user study Isabella and
Tammy are running.

**Interview track (Tammy / Isabella / Raymond, Garrison).** Not my lane, but relevant: the
post-interview analysis will surface real student pain points, and those should feed back into
which behavioral states and support types actually matter. I'll watch for that.

---

## 3. Status

Done: repo scaffold + README + setup scripts · architecture implemented across all five stages ·
behavioral-signal taxonomy implemented and tested · model backend swappable local/API ·
end-to-end run in fallback mode.

Next: wire `extension.ts` against a live JupyterLab and build the `.vsix` · sync with Adrian
(persona/delivery) and Michael (datasets/active-file) so we don't duplicate · small model eval
(latency / cost / quality) to pick the local model · add user-study logging.

Blocked on access: I still need the repo / project board (working on it today) before I can push
and update work items.

---

## 4. One-line version

Built the behavior-aware pipeline end to end this week — editor events → a cautious
support-state classifier → persona-worded inline message, swappable local/API model — and it
lines up with Adrian's persona work (same layer), Michael's datasets (plug in as new inputs), and
Darren's usability framing (thresholds + evidence are logged and tunable).
