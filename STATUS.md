# Manufacturing Diagnostic Assistant — Status & Resume Guide

By Ishank Bhatnagar

Full original architecture doc (with diagrams): https://claude.ai/code/artifact/9433c31c-f245-476c-bfa8-0dc1225888dd

Project pitch: shop-floor diagnostic copilot for manufacturing troubleshooting, built on
Dify + custom MCP tool servers. The differentiator: when the agent can't confidently answer
(low-confidence / undocumented fault), it escalates to a human expert, and the expert's answer
gets captured and written back into the knowledge base -- a working model of Nonaka's SECI
tacit-to-explicit knowledge conversion loop. Target audience for the resume story: Honda,
Hitachi, NESIC (aligns with manufacturing/SI business + the user's HARMAN internship doing
document analysis for Honda).

## Progress

- **Phase 00** (setup, self-hosted Dify + Grok) -- done
- **Phase 01** (synthetic manufacturing-line dataset) -- done
- **Phase 02** (`manual-rag-search` MCP server) -- done, registered + authorized in Dify
- **Phase 03** (`symptom-analysis` MCP server, OCR) -- done. Registered + connected in Dify
  (Integrations -> MCP), smoke test re-verified against all 4 synthetic fault images.
- **Phase 04** -- decided/skipped, see roadmap below (not redundant work, an explicit call).
- **Phase 05** (Dify diagnostic agent workflow) -- DONE and published 2026-07-18, including the
  image/OCR branch. App: "Manufacturing Diagnostic Assistant" (chatflow, app id
  `d3b1160b-bbe5-4a90-8b32-8416bb09ebf9`), public chat URL `http://localhost/chat/fTjCIHW4YTvIY8T4`.
  Verified end-to-end with real chat turns: documented faults (VFD-01, PNU-01) get a confident
  cited answer; a genuinely undocumented symptom (gearbox heat/smell, not in the fault catalog)
  correctly escalates instead of guessing; a photo-only symptom (no error code typed, just an
  uploaded display photo) correctly OCRs the code and grounds the diagnosis. See "Phase 05
  architecture" below, and "Phase 05 gotchas" for the DSL-editing workflow used to build it and
  the file-upload-input discovery trick.
- **Phase 06** (`escalation-ticketing` MCP server) -- DONE and published 2026-07-18. Registered
  + connected in Dify, wired into the diagnostic agent's escalate branch. See "Phase 06
  architecture" below.
- **Phase 07** (`knowledge-ingestion` MCP server, SECI loop) -- DONE 2026-07-18, and **verified
  closing the loop end-to-end through live Dify chat** -- see "Phase 07 architecture" below for
  the walkthrough. This is the project's core differentiator actually working, not just built.
  Registered + connected in Dify (not wired into the diagnostic chatflow itself -- meant to be
  called from the future Phase 10 expert dashboard; registering now for when that exists).
- **Phase 08** (eval harness + CI) -- DONE 2026-07-18. Two full runs of the 36-scenario harness
  found real (reproducible) accuracy issues worth knowing about, not just infra flakiness --
  see "Phase 08 findings" below. This is the most useful thing to read before touching the LLM
  prompt/confidence logic again.
- **Phase 09** (Langfuse observability) -- DONE 2026-07-19. Self-hosted Langfuse running via
  `~/projects/langfuse-platform` (separate compose project, config already existed from an
  earlier session -- see "Phase 09 architecture" below), wired into the diagnostic agent's
  built-in Dify tracing integration. Verified live: two real chat runs both produced traces in
  Langfuse, including a failed run (Groq timeout, correctly captured with `status: failed`) and
  a successful GBX-01 run with all 7 workflow-node observations. See "Phase 09 architecture" for
  how tracing was actually wired (not via the Studio UI -- it was unusable under this machine's
  resource load, so it was done via a script run inside the `api` container using Dify's own
  internal service code) and "Phase 09 gotchas" for the resource-contention issues hit along the way.
- **Phase 10** (dual-role frontend, backend bridge, containerization) -- DONE 2026-07-20 (mostly
  -- one known gap, see below). Built: a consolidated frontend (`frontend/`, Vite+React, two
  tabs: technician chat + expert dashboard) talking to a new thin FastAPI `backend/` that proxies
  Dify's Chat API (with retry logic for the known Groq-timeout gotcha) and imports
  `ticketing.py`/`capture.py` directly rather than over MCP. Verified end-to-end locally: a real
  technician query got a real Dify answer through the backend proxy, and a real ticket resolve
  went through the full capture-and-reindex flow (test data cleaned up afterward). Also wrote
  Dockerfiles for all 4 MCP servers + backend + frontend and a root `docker-compose.yml` (Dify
  itself deliberately stays a separate compose project, see README). All 6 images build
  successfully; 5 of 6 containers (backend, frontend, escalation-ticketing, knowledge-ingestion,
  symptom-analysis) verified working when run via `docker compose up`. **Known gap:
  manual-rag-search's container hit repeated network failures downloading its embedding model
  fresh (no local cache like the other approach has) during this session's testing** -- added a
  named volume for the HF cache to fix this for next time, but didn't get a final clean run to
  confirm before stopping (see "Phase 10 gotchas"). The identical code/model works reliably in
  the non-containerized local setup, so this isn't a code defect, just unverified under this
  session's network conditions. Retry `docker compose up -d --build manual-rag-search` next time
  and it should either work cleanly or fail fast and clearly if the network is still bad.

## Phase 05 architecture (as built)

Chatflow graph:
```
Start -> Has Image (IF/ELSE: sys.files not empty)
  true  -> Get Image URL (code) -> analyze_symptom_image (MCP tool) -> Format OCR Suffix (template)
  false -> Empty OCR Suffix (template, static "")
  both  -> OCR Suffix Aggregator (variable-aggregator, single group, output var "output")
       -> search_manuals_and_incidents (query = sys.query + aggregator.output)
       -> LLM -> Parse Decision (code) -> IF/ELSE -> {Answer, Answer (Escalate)}
```

- **LLM node** system prompt feeds it the symptom (`{{#sys.query#}}`) and the retrieval tool's
  text (`{{#<tool_node_id>.text#}}`), and forces a strict 2-line reply format:
  `DECISION: ANSWER|ESCALATE` / `RESPONSE: <text>`.
- **Parse Decision** (Python code node) regex-free line parse of that format into two clean
  output vars, `decision` and `response_text` -- this is what keeps the `DECISION:`/`RESPONSE:`
  scaffolding out of what the technician actually sees.
- **IF/ELSE** branches on `decision contains "ESCALATE"` to two separate Answer nodes (the
  escalate one just prepends a routing notice) -- both reference
  `{{#parse_decision.response_text#}}`.
- Confidence signal is currently just "does the LLM say ANSWER or ESCALATE", based on its own
  read of the retrieved passages -- not a hard numeric threshold on retrieval score like the
  original plan sketched. Worked well in testing (correctly escalated an undocumented gearbox
  smell rather than confabulating), but if it proves too permissive/strict in Phase 08 eval,
  consider passing the tool's actual similarity scores into the prompt explicitly.
- **Image branch**: `Has Image` checks `sys.files` (the chat's File Upload feature, enabled in
  Features -> File Upload, image type, local/URL, max 1) with comparison `not empty`. `Get Image
  URL` (code node) pulls `files[0].url` defensively (handles both dict and attribute access,
  since the exact serialization Dify hands to the sandbox wasn't worth pinning down further once
  this worked). `analyze_symptom_image`'s `image` param is a plain string (file path or base64 in
  the tool's own signature) -- **`ocr.py` was extended to also fetch `http(s)://` URLs** (stdlib
  `urllib.request`, no new dependency) since Dify's file URLs are neither a local path nor base64.
  `Format OCR Suffix` is a Jinja2 template-transform node that wraps the OCR text (or renders
  empty if OCR found nothing legible) so the aggregator's output can be appended directly onto
  the search query with no separate empty-string special-casing needed downstream.

## Phase 06 architecture (as built)

New MCP server `mcp-servers/escalation-ticketing/` (port 8003), two tools: `open_escalation_ticket` (symptom_report, ai_notes, retrieved_context -- last two
optional) and `list_open_escalation_tickets`. Tickets are one JSON file per ticket under
`data/tickets/`, id format `TKT-<UTC timestamp>-<4 hex>`. `open_escalation_ticket` regex-scans
`ai_notes + retrieved_context` for `fault_mode_id`-shaped tokens (`[A-Z]{2,5}-\d{2}`) and stores
any matches as `related_fault_mode_ids` -- useful context for the human expert even though by
definition none matched confidently enough to auto-answer.

Wired into the workflow graph: `branch (true/ESCALATE) -> ticket_tool
(open_escalation_ticket) -> Answer (Escalate)`. The escalate Answer node now shows
`{{#ticket_tool.text#}}` (the tool's own confirmation string, e.g. "Ticket TKT-... opened...
Related fault mode IDs: MTR-01, SEN-01") followed by `{{#parse_decision.response_text#}}` (the
LLM's own explanation). No dashboard yet (Phase 10) -- this is storage + tool layer only.

## Phase 06 gotchas (don't re-debug these)

- **A leading `/` character before a `{{#node.var#}}` reference in a tool node's `mixed`-type
  `tool_parameters` value gets passed through literally** to the actual MCP tool call -- e.g.
  `value: /{{#sys.query#}}` resolves to `"/Gearbox is running hotter..."`, not
  `"Gearbox is running hotter..."`. This bit us on `ticket_tool`'s three params (all copied
  verbatim from Dify's own auto-generated `/{{#sys.query#}}` pattern seen in `search_tool`'s
  query and `ocr_tool`'s image params) -- confirmed via directly inspecting a stored ticket
  JSON's `symptom_report` field. Oddly the `analyze_symptom_image` and `search_manuals_and_incidents`
  calls that use the identical `/{{#var#}}` pattern still worked correctly (OCR fetched the right
  URL, search matched the right passages) -- never fully explained why those tolerate it and this
  one didn't; simplest theory is downstream robustness (embedding search doesn't care about a
  stray leading slash; `Path(image).exists()` and the base64/URL fallback chain in `ocr.py`
  apparently still resolved correctly despite it). **Just don't copy that leading `/` when
  hand-writing DSL tool_parameters** -- use `value: '{{#node.var#}}'` with no prefix; confirmed
  clean when written that way.
- **The "first LLM call after idle times out" gotcha logged under Phase 05 was misdiagnosed.**
  Actual root cause, found while debugging repeated `HTTPSConnectionPool(...): Read timed out`
  errors during Phase 06 testing: it's not the `api` container's connectivity (that was a red
  herring -- `docker exec docker-api-1 curl https://api.groq.com` reliably succeeds) and it's not
  IPv6 either (added `sysctls: [net.ipv6.conf.all.disable_ipv6=1]` to the `api` service in
  `dify-platform/docker/docker-compose.yaml` as a first fix attempt -- harmless, left in, but
  didn't actually fix it). Dify's Groq calls are actually made from the **`plugin_daemon`**
  container (Groq is a marketplace plugin provider, `langgenius/groq`), not `api`. When the
  chat repeatedly times out, check connectivity from there instead:
  `docker exec docker-plugin_daemon-1 curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' --max-time 6 https://api.groq.com/openai/v1/models`.
  If that also hangs/fails despite the host having fine internet, it's Docker Desktop's
  WSL2 network stack getting into a bad state (external egress from containers breaks while the
  host and inter-container traffic keep working) -- **`docker compose restart plugin_daemon`**
  clears it every time this has happened so far. Not yet seen a pattern for when this occurs;
  just watch for the read-timeout error and restart that one container rather than re-pulling/
  recreating the whole stack. **But also seen it fail repeatedly (5+ times in a row) with that
  same curl succeeding fine the whole time** -- in that case it's not connectivity at all, just
  Groq itself being slow to respond within Dify's 10s read timeout on a longer prompt (more
  retrieved context = more likely to hit this). No real fix found yet beyond "keep retrying the
  same chat message"; it does eventually go through. If this becomes a recurring annoyance,
  look at whether the model/provider's read timeout is configurable in Dify (haven't checked).

## Phase 05 gotchas (don't re-debug these)

- **Dify Studio's prompt-editor variable picker crashes intermittently** (typing `{` or
  clicking the {x} insert-variable button sometimes throws "unexpected error occurred while
  rendering this component", recoverable via page reload, but any unsaved text in that field is
  lost). Root cause not identified -- possibly a race with autosave. Workaround used: build/edit
  the workflow as DSL YAML directly (Studio menu: app name dropdown -> More -> Export DSL /
  Import DSL) instead of clicking through the canvas. Export once to learn the exact schema/IDs
  for this Dify version (0.7.0 DSL, e.g. real `provider_id`/`provider_type: mcp` for our tool
  nodes -- no GUID lookup needed), then hand-edit the YAML and re-import (overwrites the draft;
  it offers a backup-current-draft option first). Validate the YAML with `yaml.safe_load` before
  importing. This is now the default way to build/extend this workflow, not a fallback.
- ~~First LLM call after any idle period reliably times out~~ -- **superseded, see the
  `Read timed out` entry under "Phase 06 gotchas" above** for the actual root cause
  (misdiagnosed here as an `api`-container/DNS issue; it's `plugin_daemon` connectivity or
  plain Groq slowness, not idle-related).
- **Importing a DSL doesn't turn on the File Upload feature toggle**, even though
  `workflow.features.file_upload.enabled: true` is set correctly in the imported YAML and the
  graph nodes (Has Image, sys.files check) all import fine. Toggle it manually after import:
  Features (top bar) -> File Upload -> on, then Settings to confirm Image is checked under
  Support File Types (it was already checked from the DSL, just the master toggle needs a
  manual flip). Re-publish after.
- **The chat input's file-attach `<input type="file">` isn't reachable directly** -- clicking
  the paperclip icon opens a small popover (URL field + "Local upload" button) and the actual
  file input only appears nested *inside* that "Local upload" button once the popover is open
  (`read_page` on the popover's dialog ref, not the top-level paperclip button, is what surfaces
  it). Don't click the paperclip/upload buttons expecting a file dialog -- open the popover, then
  `read_page filter=all` scoped to the dialog to find the real `type="file"` element.

## Phase 07 architecture (as built) -- and proof the SECI loop actually closes

New MCP server `mcp-servers/knowledge-ingestion/` (port 8004), one tool:
`capture_expert_answer(ticket_id, expert_answer, fault_mode_id="", expert_name="")`. It:
1. Looks up the ticket in `data/tickets/` for context (the original symptom report).
2. Writes a new markdown file into `knowledge-base/captured-expert-answers/` in the exact format
   `manual-rag-search/indexer.py` already expects for that folder (loaded whole, `source_type:
   captured_expert_knowledge`) -- header includes the fault mode id so the indexer's
   `[A-Z]{2,5}-\d{2}` regex picks it up automatically.
3. Reindexes by shelling out to `manual-rag-search`'s own `build_index.py` using *that server's*
   venv (`subprocess.run([manual_rag_search_venv_python, "build_index.py"], cwd=...)`) --
   deliberately avoids installing `faiss`/`sentence-transformers` a second time here.
4. Marks the ticket `status: resolved` in its JSON file (so it drops out of
   `list_open_escalation_tickets`).

**The "immediately searchable" part** (the actual point of Phase 07) needed one more piece:
`manual-rag-search/indexer.py`'s `search()` now checks the on-disk index files' mtime on every
call and auto-reloads if they changed -- so the *already-running* `manual-rag-search` server
picks up newly-captured knowledge on its very next query, no restart needed. (One gotcha while
building this: I edited `indexer.py`'s source to add that mtime check while the server was
already running from earlier in the session -- Python doesn't hot-reload already-imported module
code, only data files, so the *first* capture after adding this feature still required one
manual restart of `manual-rag-search` before the auto-reload logic itself was live. After that,
no further restarts needed.)

**Verified this actually works, live, through the full Dify pipeline** (not just unit-level):
1. Confirmed via `smoke_test.py`: "Gearbox is running hotter than usual and there's a slightly
   odd smell near the drive end" -- an undocumented symptom -- correctly escalated in Phase 05/06
   testing (tickets `TKT-20260718-151407-cab0`, then again `TKT-...-5ff9` on a later retest).
2. Ran `capture_expert_answer` with a plausible expert answer inventing fault mode `GBX-01`
   (worn gearbox output-shaft seal) against the first ticket.
3. Confirmed via direct `indexer.search()` call: the new `GBX-01` entry now scores 0.716 for that
   exact symptom -- well above the ~0.5 "confidently documented" range, and above the old
   best (mis)match (MTR-01 at ~0.44, which is why it used to escalate).
4. **Re-sent the identical chat message to the live, already-running Dify app** (no restart of
   Dify itself, no republish) and got a confident **Answer** citing "fault mode GBX-01" with the
   captured expert's actual fix steps -- the same query that escalated twice before now answers
   directly. This is the resume story's core claim, actually demonstrated working end to end.

## Phase 08 architecture and findings (eval harness + CI)

Two tiers, in `eval/` -- see `eval/README.md` for the full rationale:
- `test_kb_integrity.py` (pytest) + `eval_ocr.py`: pure Python, no Docker/Dify/Groq needed,
  **these run in CI** (`.github/workflows/eval.yml`, two jobs). Both pass cleanly (12/12 pytest
  checks; all 4 synthetic fault images OCR correctly).
- `run_scenarios.py`: sends all 36 `scenarios.json` cases through the live, published app over
  Dify's Chat API (`POST /v1/chat-messages`, blocking mode, API key from Studio -> API Access,
  stored in `eval/.env`, gitignored). **Not run in CI** -- needs the full local stack + a real
  Groq key + tolerates the known intermittent read-timeout (see Phase 06 gotchas); not practical
  or honest to fake up in a hosted runner. Run manually: `eval/results/*.json` (gitignored) holds
  full raw output including every response text, for whenever you want to re-dig into this.
- `eval_ocr.py` originally did strict substring matching against `manifest.json`'s
  `expected_text_contains` and **failed on `mtr01_display.png`** even though EasyOCR read the
  display correctly ("TRIP", "OL", "MOTOR", "THERMAL" as separate detected regions, different
  order than the expected phrase). Fixed to check word-presence order-independently, since that's
  what actually matters -- the OCR text gets joined into an embedding search query downstream,
  where word order doesn't affect matching. A strict phrase match was testing something that
  doesn't reflect real usage.

**Ran `run_scenarios.py` twice** (results `run_1784392214.json` and `run_1784393343.json`,
2026-07-18) to separate real signal from noise: 25/36 (69%) then 26/36 (72%). Diffing the two:

- **5 scenarios failed identically both times** -- genuine, reproducible behavior, not flakiness:
  `VFD-01-S3`, `SEN-01-S1`, `SEN-01-S3`, `BRG-01-S1`, `GND-01-S3`. Reading the actual answers
  reveals **two distinct real failure patterns**, both traceable to the "LLM judges its own
  confidence" design noted as an open item back in Phase 05:
  1. **Over-conservative escalation on paraphrased documented faults.** For `VFD-01-S3`/
     `SEN-01-S1`/`SEN-01-S3`, the model's own answer text *correctly names the right fault mode*
     (e.g. "I see an E003 over-current fault... but the information match is low -- I'm routing
     this to a human expert") and then escalates anyway. It knows the answer but doesn't trust
     the retrieval score enough to commit. These symptom phrasings are more indirect/paraphrased
     than the ones baked into the manuals -- lower embedding similarity even though the fault is
     still identifiable.
  2. **Overconfident misdiagnosis on undocumented faults that are superficially similar to a
     documented one.** `BRG-01-S1` ("high-pitched whine at drive end", true cause: bearing wear,
     undocumented) got confidently answered as `CNV-01` (belt slippage) -- a different, real,
     but *wrong* diagnosis, because CNV-01's documented symptoms ("rhythmic squeal", "drive end")
     are close enough in embedding space to pull a misleadingly strong match. Same pattern for
     `GND-01-S3` (grounding/static issue, misdiagnosed as `SEN-01` sensor misalignment). This is
     the more concerning failure mode of the two -- confidently wrong beats "I don't know," and
     it's exactly the risk a stricter numeric confidence threshold (rather than pure LLM
     self-judgment) would catch.
  - **This is concrete evidence for the fix already flagged in "Phase 05 architecture":** feed
    the retrieval tool's actual similarity scores into the LLM prompt explicitly (or gate on a
    hard score threshold before even asking the LLM to judge) rather than relying only on the
    model's self-reported confidence. Not yet implemented -- next thing to try if picking this
    back up.
- **3 scenarios flip-flopped pass/fail between the two runs**: `ELEC-01-S2`, `VFD-02-S1`,
  `VFD-02-S2`. This is real run-to-run non-determinism, not a bug -- the LLM node runs at
  `temperature: 0.7` (see Phase 05 architecture), so the same input can legitimately get a
  different escalate/answer judgment call to call. Worth knowing the eval accuracy number has
  some inherent variance at this temperature; averaging multiple runs (or lowering temperature
  for this specific judgment step) would give a tighter number.
- **Errors were all the known Groq read-timeout gotcha** (different scenarios each run, no
  overlap between the two runs' error sets -- confirms it's genuinely random infra flakiness,
  not something wrong with specific scenario content). Surfaces as HTTP 400 `invalid_param` via
  the REST API (vs. an inline chat error bubble in the browser UI) -- same root cause, new
  presentation, now documented in case it's confusing next time.
- **Phase 07 growth confirmed again, automatically**: `GBX-01-S1` (and `GBX-01-S2` in run 2)
  correctly flipped from the scenario file's original `escalate` expectation to `answer` --
  `run_scenarios.py` detects this itself (scans `captured-expert-answers/` for the fault mode id)
  and scores it as a pass, not a regression.

## Phase 09 architecture (as built)

Self-hosted Langfuse lives at `~/projects/langfuse-platform/` (separate compose project from
both `denshoai/` and `dify-platform/`, official `langfuse/langfuse` compose: postgres, redis,
clickhouse, minio, langfuse-web, langfuse-worker). Its `.env` was **already fully configured**
from an earlier session before this one started -- real secrets, and an org/project/user
pre-seeded via Langfuse's `LANGFUSE_INIT_*` env vars (org id `denshoai`, project id
`densho-diagnostic-agent` -- these are just internal slugs, both display names were later
updated to "Manufacturing Diagnostic Assistant" when the project was renamed, see below -- API
keys already generated). Nothing needed to be created from scratch; the work this session was
getting it running again and actually wiring it into Dify.

**Wiring tracing into Dify was done via code, not the Studio UI**, because the UI was unusable
under this machine's resource load (see gotchas below). Dify's tracing config for an app is
**two separate pieces of state**, both needed:
1. `trace_app_config` table row (the credentials) -- created via
   `services.ops_service.OpsService.create_tracing_app_config(app_id, "langfuse", {"public_key":
   ..., "secret_key": ..., "host": "http://host.docker.internal:3000"}, session=db.session())`.
   This is the same function the UI's save button calls -- it validates the credentials by
   actually pinging Langfuse (via the `ssrf_proxy` -> `host.docker.internal` path already fixed
   for the MCP servers), encrypts the keys with the tenant's key, and inserts the row.
2. `apps.tracing` column (the enabled/on-off flag + which provider) -- **easy to miss**, this is
   a *separate* field from `trace_app_config` and isn't set by `create_tracing_app_config`. Set
   via `core.ops.ops_trace_manager.OpsTraceManager.update_app_tracing_config(app_id, enabled=True,
   tracing_provider="langfuse")`. Without this second call, traces silently never get submitted --
   no error anywhere, `trace_app_config` looks fully populated and correct, chat still works
   normally, there's just no trace in Langfuse and nothing in the logs saying why.

Both calls were run as one-off scripts copied into the `api` container (`docker cp` +
`docker exec ... .venv/bin/python script.py`) using Dify's own `app_factory.create_app()` (note:
returns a `(socketio_app, flask_app)` tuple, not the app directly) for a real Flask app context,
then removed after running. This is the direct-DB/service-layer equivalent of clicking through
the Studio UI's "Tracing app performance" panel -- same validation, same encryption, same result.

**Verified working end-to-end**: sent two live chat messages via the Chat API
(`POST /v1/chat-messages`, same pattern as `eval/run_scenarios.py`). One hit the known Groq
read-timeout gotcha and Langfuse correctly recorded it as a trace with `status: failed`, 0 tokens.
The other (the standard GBX-01 gearbox-smell scenario from Phase 07's walkthrough) succeeded and
produced a full trace with 7 observations (one per workflow node -- this is the "tool-call
sequence" tracing this phase was meant to deliver), input/output, token usage, and latency, all
visible via `GET /api/public/traces` and presumably the Langfuse UI (not visually confirmed --
see gotchas).

## Phase 09 gotchas (don't re-debug these)

- **This machine (7.6GB RAM) genuinely struggles to run the full Dify stack + full Langfuse
  stack at the same time.** Not a bug, a real capacity limit -- expect this every time both are
  brought up together, not just once. Symptoms seen this session: `langfuse-web`'s host port
  (3000) stopped responding while the container itself was completely healthy (confirmed via
  `docker exec` into another container and hitting `langfuse-web:3000` directly on the Docker
  network -- got an instant `200`) -- this was the host<->WSL2 port-forwarding layer
  (`wslrelay.exe`) getting stuck, not the app. Fix: `docker compose restart langfuse-web` (just
  that container, not the whole stack) re-establishes the binding. Also saw `langfuse-worker`
  repeatedly log `Socket timeout. Expecting data, but didn't receive any in 30000ms` against its
  own `redis` container, even though direct `redis-cli ping` from another container returned
  `PONG` instantly -- this is Node's event loop being CPU-starved past Redis's response window,
  not an actual network/Redis problem. It clears up once overall CPU load drops; don't chase it
  as a connectivity bug.
- **`~/.wslconfig`'s `processors` cap fights with Langfuse specifically.** The RAM-crash fix from
  earlier this session (see "Steps to resume after a reboot") originally set `processors=2`,
  which was fine for Dify alone but caused ClickHouse (Langfuse's OLAP store) to peg past 100% CPU
  and take 10+ minutes to finish its startup migrations. Bumped to `processors=4` (host has 8
  cores/16 threads, plenty of headroom -- checked host-wide CPU% before doing this) and it
  finished in a couple minutes instead. Changing this requires a full `wsl --shutdown` +
  Docker Desktop relaunch, which takes the whole Dify stack down too (needs the same
  Postgres-slow-to-sync + `api`/`plugin_daemon` restart dance documented under "Steps to resume
  after a reboot" -- did it twice this session for exactly this reason).
- **The Chrome extension (`claude-in-chrome`) became unreliable once both stacks were running
  under memory pressure** -- screenshots failed with a `params.clip.scale` deserialization error,
  `read_page` returned `Viewport: 0x0`, tabs randomly lost their ID between calls, and eventually
  a `Cannot access contents of the page` permission error appeared on a freshly-created tab. Not
  investigated further since the DB/service-layer approach above worked and was more reliable
  anyway -- but if picking this project back up and the browser tool is needed (e.g. for actually
  building things in Dify Studio, not just flipping one config), worth checking free RAM first
  and/or closing one of the two stacks temporarily rather than assuming the extension itself is
  broken.
- **Never visually confirmed the Langfuse UI itself renders traces correctly** (only confirmed via
  its REST API, `GET /api/public/traces`) -- the browser issues above prevented it. Worth a quick
  look next time the browser tool is working, just to eyeball the trace waterfall/timeline view
  actually looks right, not just that the data landed.

## Phase 10 architecture (as built)

`backend/main.py` (FastAPI, port 8005): `GET /api/tickets` and `POST /api/tickets/{id}/resolve`
import `ticketing.py`/`capture.py` directly (both stdlib-only -- no MCP protocol needed for a
web frontend to use them); `POST /api/chat` proxies Dify's Chat API with the API key held
server-side and the same retry/backoff pattern as `eval/run_scenarios.py`, plus file-upload
support (uploads to Dify's `/files/upload` first, then references the returned `upload_file_id`
in the chat call). `frontend/` is a single Vite+React app, two tabs (technician / expert), no
router needed given the small surface area.

Containerization (`docker-compose.yml` + one `Dockerfile` per service): the tricky part was that
`capture.py`'s reindex step shells out to `manual-rag-search/build_index.py`, which in local dev
reuses that server's own venv (`MANUAL_RAG_VENV_PYTHON`) -- doesn't exist in a container, so
`capture.py` now falls back to `sys.executable` (see its `_rebuild_search_index`), and
`knowledge-ingestion`/`backend`'s Dockerfiles install `manual-rag-search`'s (heavier) deps
themselves rather than trying to share a venv across container boundaries. The three services
that touch `knowledge-base/` (`manual-rag-search`, `knowledge-ingestion`, `backend`) all bake a
copy of it into their image -- necessary so the shared `knowledge_base` named volume seeds
correctly on first run (Docker only auto-populates an empty named volume from the *mounting
container's own image content* at that path, so every image touching that volume needs the
content, not just one).

## Phase 10 gotchas (don't re-debug these)

- **Building with default `pip install` pulls full CUDA-enabled torch** (many `nvidia-*`
  packages, ~15 min build + huge image) even though this machine has no GPU to use it. Fixed by
  adding `--extra-index-url https://download.pytorch.org/whl/cpu` plus an explicit `torch` line
  to `manual-rag-search/requirements.txt` and `symptom-analysis/requirements.txt` -- cut rebuild
  time to ~1-2 min once cached and meaningfully smaller images. If a fresh build seems to be
  taking 10+ minutes, check whether this line is still there before assuming something's wrong.
- **A stale/empty named volume doesn't self-heal just by fixing the Dockerfile.** After adding
  `knowledge-base/` to the affected Dockerfiles, `manual-rag-search` still crashed with "No
  knowledge-base content found" until the already-created empty `denshoai_knowledge_base` volume
  was explicitly removed (`docker volume rm`) so Compose would recreate and re-seed it from the
  now-fixed image. Rebuilding the image alone does nothing to an existing volume's contents.
- **`docker restart` on a container with a corrupted/partial download in its filesystem just
  keeps failing the same way** -- it reuses the same container filesystem, so a bad
  HuggingFace-cache download from a flaky-network attempt persists across restarts. Needed
  `docker compose up -d --force-recreate <service>` (or `down` + `up`) to actually get a fresh
  filesystem and retry the download cleanly. Even then, this session kept hitting genuine network
  drops (`RuntimeError: Cannot send a request, as the client has been closed`) trying to reach
  huggingface.co for `manual-rag-search`'s embedding model -- unclear whether that's this
  machine's general network flakiness (see Phase 06's Groq-timeout gotcha for a similar pattern
  with a different host) or something specific to that model repo; added a named volume
  (`hf_cache` -> `/root/.cache/huggingface`, shared across `manual-rag-search`,
  `knowledge-ingestion`, and `backend`) so that once *any* one of them successfully downloads it,
  the others reuse it and restarts stop re-triggering the download -- but this fix itself wasn't
  re-verified with a clean run before stopping for the session. Retry first before assuming it's
  broken again.

## Steps to resume after a reboot

(Resolved 2026-07-18: Docker Desktop's engine had gotten wedged after force-killing/relaunching
it; a full reboot fixed it. Stack is back up -- Postgres needed ~25s to finish a post-reboot
disk sync before going healthy, and nginx needed a manual restart to pick up new container IPs
for `web`/`plugin_daemon` after they got recreated. Both MCP servers restarted clean, single PID
each. Leaving these steps below for the next time this happens.)

(Resolved 2026-07-20, after a RAM/Docker crash: host only has 7.6GB total RAM, no `.wslconfig`
existed, so WSL2/Docker had no cap and could starve Windows itself -- likely root cause of the
crash. Fix: added `~/.wslconfig` (`memory=4.5GB`, `swap=4GB`, `processors=2`), then `wsl --shutdown`
to apply. Also discovered a full **Langfuse stack** (`langfuse-platform`, web/worker/postgres/
redis/clickhouse/minio, ~1.3GB) auto-starting via Docker's restart policy even though Phase 09 was
never actually started -- stopped it (`docker compose -p langfuse-platform stop`) to relieve
memory/CPU contention; this was blocking `api` from going healthy. Same Postgres-slow-to-sync
pattern as 2026-07-18 recurred (worse this time, ~90s+) and needed the same `api`/`plugin_daemon`
restart-after-healthy fix. If resuming again on this machine: expect this Postgres delay, don't
be alarmed by it, and check `docker ps` for any unexpected auto-started stacks (anything with a
`restart: unless-stopped` policy from a prior session) competing for the now-capped 4.5GB before
assuming Dify itself is broken.)

1. **Start Docker Desktop** (may auto-start; otherwise launch it, wait ~30-60s).
   Verify: `docker info` returns without hanging.

2. **Bring the Dify stack back up:**
   ```
   cd ~/projects/dify-platform/docker
   docker compose up -d
   docker compose ps      # all should show "Up" / "healthy"
   ```
   Confirm `http://localhost` loads in a browser.

3. **Restart the four local MCP servers** (plain background processes -- do NOT survive reboot):
   ```
   cd ~/projects/denshoai/mcp-servers/manual-rag-search
   $env:PYTHONIOENCODING = "utf-8"
   .\.venv\Scripts\python.exe server.py    # port 8001

   cd ~/projects/denshoai/mcp-servers/symptom-analysis
   $env:PYTHONIOENCODING = "utf-8"
   .\.venv\Scripts\python.exe server.py    # port 8002

   cd ~/projects/denshoai/mcp-servers/escalation-ticketing
   .\.venv\Scripts\python.exe server.py    # port 8003

   cd ~/projects/denshoai/mcp-servers/knowledge-ingestion
   .\.venv\Scripts\python.exe server.py    # port 8004
   ```
   Run each detached (`Start-Process ... -WindowStyle Hidden -RedirectStandardOutput/-Error ...`),
   then verify with `netstat -ano | findstr ":8001"` / `":8002"` / `":8003"` / `":8004"` (expect
   exactly one PID listening on each -- watch out for duplicate stray processes, kill and restart
   clean if so).

4. **Check all four MCP servers show as connected in Dify** (Integrations -> MCP). Dify's own
   state (registered servers, auth status) lives in Postgres and should survive untouched. If any
   is missing, add it: URL `http://host.docker.internal:<port>/mcp`, matching name, click Add &
   Authorize -- should connect cleanly first try (see gotchas below for why).

5. **If chat requests time out with `HTTPSConnectionPool(...): Read timed out`**, that's usually
   Docker Desktop's WSL2 network stack, not the app -- see the plugin_daemon gotcha under
   "Phase 06 gotchas" below. Try `docker compose restart plugin_daemon` before assuming anything
   is actually broken.

## Key technical decisions / gotchas already solved (don't re-debug these)

- **Self-hosted Dify** lives at `~/projects/dify-platform/` (official langgenius/dify clone,
  separate from this repo). This repo (`denshoai/`) holds only our own code: MCP servers,
  synthetic data, knowledge base content.
- **SSRF proxy blocking `host.docker.internal`**: Dify's Squid SSRF-protection proxy denies
  outbound requests to private IP ranges by default (403 Forbidden, looks like an auth problem
  but isn't). Fixed by adding `SSRF_PROXY_ALLOW_PRIVATE_DOMAINS=host.docker.internal` to
  `dify-platform/docker/.env` and recreating the `ssrf_proxy` container
  (`docker compose up -d --force-recreate ssrf_proxy`). Domain-based, so it covers any port --
  no further proxy config needed for additional local MCP servers.
- **MCP SDK DNS-rebinding protection**: both servers set
  `TransportSecuritySettings(enable_dns_rebinding_protection=False)` in `server.py` -- this
  protection is for internet-facing servers, not local-dev tools only reached by our own Dify
  container. See comments in each `server.py`.
- **Dify's "Authorize" button** on the MCP settings page always routes through an OAuth-specific
  endpoint (`/mcp/auth`) even for non-OAuth servers; this is normal/expected and works fine once
  the above two issues are fixed -- don't be alarmed if it briefly shows "Authorization required."
- **Windows console + EasyOCR**: EasyOCR's progress bar uses Unicode block characters that crash
  on the default Windows console codepage. Fix: set `$env:PYTHONIOENCODING = "utf-8"` before
  running anything that imports easyocr.
- **Each MCP server has its own separate `.venv`** (not shared) -- `pip install -r requirements.txt`
  reuses the local pip wheel cache so repeat `torch` installs are fast.
- **Dify session tokens expire ~hourly**; if the UI shows a weird error/redirect, just
  navigate to `http://localhost` again (usually still logged in, just needed a refresh).

## Roadmap: what's left (Phases 04-10, most now done -- see DONE markers below)

### Phase 04 -- Load knowledge base into Dify (DECIDED: skipped, see below)
Decided 2026-07-18: not loading `knowledge-base/manuals/` or `knowledge-base/incident-logs/`
into Dify's built-in Knowledge base. `manual-rag-search`'s own FAISS retrieval already covers
this content, and duplicating it into Dify Knowledge would just be two indexes of the same
data with no upside -- the MCP tool remains the sole retrieval path for fault-specific content.
Revisit only if we later add a genuinely different content type (e.g. regulation/process docs)
that isn't fault-specific.

### Phase 05 -- Dify diagnostic agent workflow (core) -- DONE, see "Phase 05 architecture" above
Both the text-only path and the image/OCR path (symptom report [+ optional photo] -> retrieval
-> confident-answer-or-escalate) are built, published, and verified end-to-end. Only known
open item: confidence signal is the LLM's own judgment call, not the numeric retrieval-score gap
originally sketched (7 documented fault modes ~0.5-0.65+, 5 undocumented ~0.45 max) -- fine for
now, revisit if Phase 08 eval shows it's too permissive/strict.

### Phase 06 -- Escalation & Ticketing MCP server -- DONE, see "Phase 06 architecture" above

### Phase 07 -- Knowledge-Ingestion MCP server (SECI loop) -- DONE, see "Phase 07 architecture" above
Core differentiator, built and verified actually closing the loop end-to-end through live Dify
chat (not just at the storage layer) -- a previously-escalating symptom now gets answered
directly after an expert answer is captured for it, no restarts needed for the new knowledge to
become searchable. Also fixed the outstanding leading-`/` DSL bug and corrected the Phase 05
timeout misdiagnosis while debugging Phase 06 along the way.

### Phase 08 -- Eval harness + CI -- DONE, see "Phase 08 architecture and findings" above
Real, useful findings, not just a green checkmark: two reproducible failure patterns identified
(over-conservative escalation on paraphrased documented faults; overconfident misdiagnosis on
undocumented faults that are superficially similar to a documented one), both pointing at the
same fix -- feed explicit retrieval similarity scores into the LLM's confidence judgment instead
of relying on self-reported confidence alone. Not yet implemented; next thing to try if revisiting
the LLM/prompt layer. Knowledge-base growth (Phase 07) reconfirmed automatically by the harness
itself. CI runs the two tiers that don't need live Dify/Groq (`test_kb_integrity.py`,
`eval_ocr.py`); the full 36-scenario live run is a manual tool against your local stack, by design
-- see `eval/README.md`.

### Phase 09 -- Observability (Langfuse) -- DONE, see "Phase 09 architecture" above
Self-hosted Langfuse via Docker Compose, trace every diagnostic run: confidence scores,
tool-call sequence, escalation rate. Tool-call sequence and per-run outcome (succeeded/failed)
confirmed working via live traces (see architecture section). Confidence-score/escalation-rate
*aggregation* isn't built as a dashboard yet -- the raw data (answer text, status, tokens) is all
in Langfuse per-trace now, so this would be a Langfuse "Scores" or a saved view/dashboard on top,
not new instrumentation. Natural next step if revisiting this phase.

### Phase 10 -- Dual-role frontend & polish -- DONE 2026-07-20, see "Phase 10 architecture" above
Technician diagnostic view + expert escalation dashboard both built and verified working
end-to-end locally. MCP servers + backend + frontend all containerized with a root
`docker-compose.yml` (Dify itself intentionally stays a separate compose project, not merged in
-- see README "Local development"). One known loose end: `manual-rag-search`'s container hit
network flakiness downloading its embedding model during this session -- see "Phase 10 gotchas".
Not done: architecture diagram and a demo recording for the README (recording in particular
needs a human at the keyboard/browser, not something to automate).

## Resume bullets (pre-written, from the original plan)

- Designed and built Denshō AI, an agentic shop-floor diagnostic copilot for manufacturing
  troubleshooting, orchestrated via Dify with custom MCP tool servers for symptom analysis,
  incident-log retrieval, and expert escalation.
- Implemented a tacit-knowledge capture loop -- modeled on Nonaka's SECI framework -- where
  expert answers to escalated cases are automatically structured and written back into the
  RAG knowledge base.
- Built a dual-role system (technician diagnostic interface + expert escalation dashboard)
  with an evaluation harness tracking both diagnostic accuracy and knowledge-base growth
  over time.
- Deployed the full stack -- Dify, MCP servers, Langfuse observability, Postgres -- via
  Docker Compose with GitHub Actions CI/CD.
