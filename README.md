# IDA — Jupyter AI in VS Code

Integration layer for the **IDA** (AI study companion) prototype: a VS Code / Jupyter
extension that watches how a student works, infers social-emotional needs from that
behavior, and delivers proactive, contextual support messages inline.

Part of the VariAbility Lab project *Supporting Neurodivergent Well-being in AI Education
and the Workforce* (Pathways for AI).

## What's here

| Path | What it is |
|------|-----------|
| `service/signals.py` | **The taxonomy, as runnable code.** events → `{state, confidence, evidence, support}`. `python signals.py` runs the scenario tests. |
| `service/orchestration.py` | state → prompt. Persona voice + per-support templates (where tone is enforced). |
| `service/backend.py` | one model interface over local vLLM (Qwen3/Llama) and the APIs (Claude/GPT). |
| `service/server.py` | ties the above together behind `POST /infer` + `POST /dismiss`. `python server.py`. |
| `src/extension.ts` | VS Code capture + proactive inline delivery — the parts that must live in the editor. |
| `docs/ARCHITECTURE.md` | short code-map + diagram (the substance is the code). |
| `docs/BEHAVIORAL_SIGNALS.md` | short why-guide pointing at `signals.py`. |
| `scripts/setup.sh` · `scripts/dev.sh` | env setup / dev loop. |
| `.env.example` | copy to `.env`; keys or local model endpoint. |

## Quick start

```bash
git clone <repo> && cd jupyter-ai-vscode
cp .env.example .env          # then edit .env
bash scripts/setup.sh
bash scripts/dev.sh
```

## Research framing (from lab meetings)

> **How might we facilitate AI-supported social-emotional learning inside a programming
> environment?**

Hypothesis — programming environments can deliver AI-generated support that:
1. **infers** user social-emotional needs from common programming-environment behavior, and
2. **responds** with contextual support messages proactively, through inline messages.

Prior lab work shows some students delegitimize the social-emotional side of software
development and avoid human support out of disinterest or rejection sensitivity. IDA's job
is to meet those students *in the environment they already trust*, without demanding they
ask for help.

## Status

- [x] Literature review on Jupyter AI persona implementation
- [x] Model shortlist (Llama, Qwen3)
- [x] Behavioral-signal taxonomy — implemented + tested in `service/signals.py`
- [x] Architecture — capture / inference / orchestration / backend / delivery scaffolded
- [x] End-to-end path runs in fallback mode with no key (`python server.py`)
- [x] Michael's frustration signal integrated as a feature input (reinforces, never triggers alone)
- [x] Study logging for the usability question (`service/study_log.py`, wired into the service)
- [x] Model eval harness (`service/eval_models.py`) — latency + tone guardrails per scenario
- [x] VS Code extension compiles clean (`tsc --noEmit` passes)
- [x] Native Jupyter AI personas — 4 `BasePersona` subclasses, one per support mode (`personas/`)
- [ ] Wire the extension against a live JupyterLab + build the `.vsix` — needs a running Jupyter host
- [ ] Run the eval against real Qwen3 / Llama / API to pick the model
- [ ] Collect real study logs during user sessions

## Open questions for the team

- Proactive (unsolicited) messaging is **not documented** in Jupyter AI. We likely need a
  thin custom VS Code extension for the *delivery* path; Jupyter AI handles the *generation*
  path. See `docs/ARCHITECTURE.md` §4.
- Behavioral sensing has consent/IRB implications (esp. anything keystroke- or
  camera-adjacent). See `docs/BEHAVIORAL_SIGNALS.md` §6 before we instrument anything.

## Contacts

Ren/Darren (PhD lead) · Adrian (technical, Jupyter AI + VS Code) · Michael (signals /
datasets) · Isabella, Tammy, Sanjana (design & user study) · Andrew Begel (PI)
