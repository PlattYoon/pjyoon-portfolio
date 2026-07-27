# IDA — Architecture (code map)

The real spec is the code. This is the two-minute orientation for anyone opening the repo.

**One idea holds the whole thing together:** Jupyter AI is request/response — the student
asks, it answers. We need the *opposite*: the system notices something and speaks first. So we
split the work into three parts and only the middle one reuses Jupyter AI:

- **sensing** + **delivery** → ours, must live in the editor → `src/extension.ts`
- **deciding what to say** → Jupyter AI persona + our templates → `service/orchestration.py`
- **the model** → local Qwen3/Llama *or* Claude/GPT, same interface → `service/backend.py`

That keeps the one genuinely-unsolved piece (proactive delivery — there's *no* upstream docs for
it) small and boxed off in `extension.ts`. Everything else uses supported APIs.

```
   VS Code / Jupyter (src/extension.ts)
   ┌───────────────────────────────────────────┐
   │  CAPTURE  edits, errors, idle, switches    │  metadata only, no source text
   │     │  events (every ~30s)                 │
   │     ▼                                      │
   └─────┼──────────────────────────────────────┘
         ▼                          Python service (service/)
   ┌───────────────┐   ┌──────────────────┐   ┌───────────────┐   ┌──────────────┐
   │ signals.py    │──►│ orchestration.py │──►│  backend.py   │──►│ Qwen3/Llama  │
   │ events→state  │   │ state→prompt     │   │ local OR api  │   │  or Claude   │
   │ (the taxonomy)│   │ (tone lives here)│   └───────────────┘   └──────────────┘
   └───────────────┘             │
         ▲                       ▼   message (or nothing)
   ┌─────┼──────────────────────────────────────┐
   │  DELIVERY  inline, rate-limited, dismissible│  (src/extension.ts, server.py glues it)
   └────────────────────────────────────────────┘
```

## Files

| File | Does |
|------|------|
| `src/extension.ts` | Capture (edits/errors/idle/focus) + delivery (inline, cooldown, dismiss). The parts that must run in-editor. |
| `service/signals.py` | events → `{state, confidence, evidence, support}`. The taxonomy. Run it: `python signals.py`. |
| `service/orchestration.py` | state → prompt. Persona voice + per-support templates. Where tone is enforced. |
| `service/backend.py` | one interface over local vLLM and the APIs. Falls back to canned lines with no key. |
| `service/server.py` | ties the three together behind `POST /infer` and `POST /dismiss`. |

## Local vs API

Same OpenAI-compatible interface for both, so switching is config, not code (`.env`):

- **API mode** — set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. Fast to iterate; data leaves the box.
- **Local mode** — run vLLM, set `MODEL_BASE_URL` + `MODEL_NAME`. Nothing leaves the box — the
  right posture once we're sensing real behavior.
- **No key** — `backend.py` returns the deterministic fallback lines, so tests run anywhere.

## Still open (for the team)

- Which surface is primary — VS Code or JupyterLab? Depends who our recruits actually use.
- Confidence thresholds + cooldown that feel *supportive* not *surveillant* — a user-study
  question as much as an engineering one.
- Which local model, specifically — needs a small latency/cost/quality eval.
- Michael's active-file blocker is handled in `extension.ts` (`onDidChangeActiveTextEditor`).

Privacy note: capture is metadata only by default; anything keystroke- or camera-adjacent is a
higher consent tier and IRB-gated. See `BEHAVIORAL_SIGNALS.md`.
