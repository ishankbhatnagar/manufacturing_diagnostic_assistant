# eval

Two tiers, deliberately split because one needs the full live stack and one
doesn't:

## 1. `test_kb_integrity.py` + `eval_ocr.py` -- runs in CI

Pure Python, no Docker/Dify/Groq required:

- `test_kb_integrity.py` (pytest): scenarios.json and manifest.json are
  well-formed, every fault mode in `fault_catalog.py` has exactly one eval
  scenario, documented fault modes have manual/incident-log coverage and
  undocumented ones don't (catches the ground truth drifting out of sync
  with the actual knowledge base), captured expert answers and tickets have
  valid schema.
- `eval_ocr.py`: runs EasyOCR against the 4 synthetic fault-display images
  and checks the expected text (error codes etc.) gets detected. Needs
  `symptom-analysis`'s deps (easyocr/torch), not this folder's -- run it
  from there:
  ```
  cd mcp-servers/symptom-analysis
  .venv\Scripts\python.exe -m pip install -r ../../eval/requirements.txt
  .venv\Scripts\python.exe ../../eval/eval_ocr.py
  ```

See `.github/workflows/eval.yml` -- these two run on every push/PR.

## 2. `run_scenarios.py` -- full end-to-end, run manually

Sends all 36 `scenarios.json` cases through the live, published Manufacturing
Diagnostic Assistant over Dify's Chat API and scores answer-vs-escalate
accuracy. **Not run in CI** -- it needs the whole local stack up (self-hosted
Dify + all four MCP servers, a real Groq API key configured in Dify, real
inference cost/latency per scenario). Spinning that up in a GitHub-hosted
runner isn't practical for a personal project (no self-hosted Dify there,
no secrets wired up, and we've directly hit intermittent Groq read-timeouts
locally -- see STATUS.md gotchas -- that would make CI flaky). This is the
honest scope: test what's deterministic and free in CI, keep the expensive
live-LLM eval as a local/manual tool run against your own instance.

```
cd eval
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env    # then fill in DIFY_API_KEY from Studio > API Access
.venv\Scripts\python.exe run_scenarios.py
```

Reports pass/fail per scenario plus a summary (documented vs. undocumented
accuracy, how many answers explicitly cited the right fault mode id).
Automatically detects scenarios whose fault mode now has a captured expert
answer (Phase 07) and scores those as passing if they *now* answer instead
of escalating -- that's the SECI loop working, not a regression. Full
results (including every response text) are written to
`eval/results/run_<timestamp>.json` (gitignored).
