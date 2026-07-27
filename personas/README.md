# IDA Personas — native Jupyter AI personas

Four **real Jupyter AI personas**, one per IDA support mode. Unlike the prompt
layer in `../service`, these subclass `BasePersona`, register via entry points,
and appear as @-mentionable assistants in the Jupyter AI chat.

| @-mention | serves state | for the student who... |
|-----------|--------------|------------------------|
| `@IDA-Unblock` | `stuck` | is circling one concrete error and needs the next step |
| `@IDA-Focus` | `overwhelmed` | is scattered across the notebook and needs structure |
| `@IDA-Nearby` | `withdrawn` | is struggling but won't ask — the gentlest, optional presence |
| `@IDA-Checkin` | `disengaged` | drifted off; a light, easy-to-ignore check-in |

All four share one voice and one set of tone rules (`base.py` → `SHARED_RULES`):
describe the situation not the person, one short optional step, no "you should",
no exclamation marks, effortless to ignore. They differ only in framing.

## On-demand vs. proactive

These personas are the **on-demand** side of IDA — the student @-mentions them.
The **proactive** side (noticing without being asked) is the delivery service in
`../service`, which infers a state from behavior and speaks first. Both use the
same four voices, so a student gets a consistent IDA whether they reached out or
IDA did. Jupyter AI personas only reply when @-mentioned, which is exactly why the
proactive path has to live outside the persona framework.

## Install & register

```bash
cd personas
pip install .            # or: pip install -e .[api]   /   .[local]
# restart JupyterLab — the four personas appear in the chat's @ menu
```

Pick a model backend via env (same knobs as the service):

```bash
export ANTHROPIC_API_KEY=...            # API mode
# or
export MODEL_BASE_URL=http://localhost:8000/v1 MODEL_NAME=Qwen3-32B   # local vLLM
```

With no key set, each persona replies with its own hand-written fallback line, so
they still work for a dry run.

### Fast local dev (no reinstall)

Drop any of these into `.jupyter/personas/` (filename must contain "persona"),
then run `/refresh-personas` in a chat to reload without restarting JupyterLab.

## Files

| File | What |
|------|------|
| `ida_personas/base.py` | `IdaBasePersona` — the shared voice, model call, `process_message` |
| `ida_personas/personas.py` | the four concrete personas |
| `ida_personas/model.py` | model backend (local / API / fallback), no Jupyter dependency |
| `ida_personas/assets/*.svg` | avatars, palette-matched to each support mode |
| `pyproject.toml` | `[project.entry-points."jupyter_ai.personas"]` registration |

## Note on testing

The persona classes are written against the documented `BasePersona` /
`PersonaDefaults` / `process_message` API and verified by introspection with the
Jupyter deps stubbed; `model.py` runs standalone. End-to-end @-mention behavior
still needs a live JupyterLab + Jupyter AI v3 install to confirm — that's the one
step that can't be exercised offline.
