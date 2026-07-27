# Running IDA

Four ways to run this, fastest first. The inference brain is pure Python standard
library, so you can see it work with zero install.

---

## 0. Get the code

```bash
unzip jupyter-ai-vscode.zip
cd jupyter-ai-vscode
```

---

## 1. See the brain work — no install, ~5 seconds

The behavioral-signal classifier has no dependencies. Run its scenario tests:

```bash
cd service
python3 signals.py
```

Expected: six labelled scenarios print what each situation maps to, ending in
`all scenarios passed.`

```
[stuck]       0.75  «same error 4x on one cell» -> unblock
[overwhelmed] 0.89  «lots of deleting and re-running... not much landing» -> structure
[withdrawn]   0.95  «kept hitting errors without opening help, then stepped away» -> low_pressure_offer
[disengaged]  saw it (0.68 < floor) but held back — a break isn't a problem to fix ✔
[silence]     stayed quiet ✔
[dismissed]   respected the brush-off ✔
all scenarios passed.
```

This is the quickest proof the taxonomy works. **Run this yourself before telling
anyone "it runs" — so the claim is firsthand.**

---

## 2. Run the full service loop — no keys, canned messages

Still standard-library only. From `service/`:

```bash
python3 server.py          # local service on http://localhost:8770
```

In a second terminal, send it a "stuck" trace and watch it respond:

```bash
python3 - <<'PY'
import json, time, urllib.request
now = time.time()
events = [{"t": now-5+i, "type":"cell_run",
           "data":{"status":"error","error_type":"NameError",
                   "cell_id":"c3","consecutive_failures":i+1}} for i in range(4)]
events.append({"t": now, "type":"help_opened", "data":{}})  # they opened help -> 'stuck', not 'withdrawn'
req = urllib.request.Request("http://localhost:8770/infer",
        data=json.dumps({"events": events}).encode(),
        headers={"content-type":"application/json"})
print(urllib.request.urlopen(req).read().decode())
PY
```

You'll get JSON back with `state: stuck` and a support message. Drop the
`help_opened` line and it flips to `withdrawn` — that's the `help_avoidance` logic
working, and a nice thing to show the team.

Endpoints: `POST /infer {events:[...]}` and `POST /dismiss {state}`.

---

## 3. Add a real model — optional

```bash
cp .env.example .env
```

Then edit `.env` and pick one:

- **API mode:** set `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`).
- **Local mode:** run a vLLM server, set `MODEL_BASE_URL` + `MODEL_NAME`
  (e.g. `Qwen3-32B-AWQ`). Nothing leaves the machine.

Re-run `python3 server.py` — it now words messages with the model instead of the
fallback lines. No key = it just keeps using fallbacks, so this step is optional.

---

## 4. Full environment for the real Jupyter integration

From the repo root:

```bash
bash scripts/setup.sh      # venv + jupyterlab + jupyter-ai + deps
bash scripts/dev.sh        # JupyterLab with Jupyter AI on :8888
```

---

## Regenerate the demo video

```bash
python3 scripts/make_demo.py    # re-renders docs/ida_demo.mp4 from live signals.py output
```

---

## Run it live in VS Code (wired end-to-end)

The extension is installed and self-sufficient — it starts the Python brain itself,
so there's no separate terminal to babysit.

1. Open this folder in VS Code (the workspace `.vscode/settings.json` turns IDA on
   and sets a short `ida.minGapSeconds` for testing).
2. **Developer: Reload Window** (Command Palette) if it was already open. You'll see
   a one-time "IDA active — proactive help is ON" toast.
3. Open `ida_demo.ipynb`, pick the `.venv` kernel, and run the failing cell a few
   times. Within a few seconds IDA offers help inline — unprompted. This works for
   *any* cell you write, not just the demo one (the fail-streak is tracked per cell).
4. It keeps running the whole session: if the service ever dies it's respawned on the
   next poll, and it's shut down cleanly when you close VS Code.

Wellbeing: after a long heads-down stretch with no break (~40 min+, and firmly by an
hour) IDA gently checks in and suggests a pause — the care side, not just the
"you're stuck" side. Reset happens automatically when you step away for 5+ minutes.

Rebuild after editing `src/extension.ts`:

```powershell
cd src; node node_modules\typescript\bin\tsc -p ./
# then copy package.json + out\ into %USERPROFILE%\.vscode\extensions\variability-lab.ida-vscode-0.1.0\
```

---

## Where things live

| Path | What |
|------|------|
| `service/signals.py` | the behavioral-signal classifier (the taxonomy) |
| `service/orchestration.py` | state → prompt (persona voice + templates) |
| `service/backend.py` | model interface (local vLLM / API / fallback) |
| `service/server.py` | ties them together behind `/infer` + `/dismiss` |
| `src/extension.ts` | VS Code capture + inline delivery |
| `docs/ARCHITECTURE.md` | code map + diagram |
| `docs/BEHAVIORAL_SIGNALS.md` | the why behind `signals.py` |
| `docs/WEEKLY_SUMMARY.md` | this week's work + how it fits the team |
| `docs/ida_demo.mp4` | 59s animated walkthrough |

---

## Model eval (pick the local model)

```bash
cd service
python3 eval_models.py                 # runs frustration scenarios through the current backend
# ANTHROPIC_API_KEY=...  or  MODEL_BASE_URL=... MODEL_NAME=...  to eval a real model
```

Prints per-scenario latency, tone guardrail checks, and the message — so you can
lay Qwen3 / Llama / API side by side and choose with evidence.

## Study logs (the usability data)

Every decision (including deliberate silences) and every student response is
appended as JSONL to `service/study_events.jsonl` (override with `IDA_STUDY_LOG`).
Roll it up any time:

```bash
python3 -c "import study_log,pprint; pprint.pprint(study_log.summarize())"
```

Gives per-state shown / engaged / ignored / dismissed counts and a dismissal rate
(our false-positive proxy).

## Compile the VS Code extension

```bash
cd src
npm install
npx tsc --noEmit        # type-checks; drop --noEmit to emit out/extension.js
```

Compiles clean today. Running it live still needs loading into a VS Code
extension host connected to a Jupyter session (the last integration step).

---

## Install the Jupyter AI personas (@-mention side)

Four native Jupyter AI personas, one per support mode, live in `personas/`.

```bash
cd personas
pip install .              # registers @IDA-Unblock / @IDA-Focus / @IDA-Nearby / @IDA-Checkin
# restart JupyterLab, then @-mention them in the Jupyter AI chat
```

Model backend uses the same env knobs as the service (`ANTHROPIC_API_KEY`, or
`MODEL_BASE_URL` + `MODEL_NAME`); with none set they use hand-written fallback
replies. Needs Jupyter AI v3 (`jupyter-ai-persona-manager`). For fast iteration,
drop the persona files into `.jupyter/personas/` and run `/refresh-personas`.
