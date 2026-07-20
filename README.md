# Manufacturing Diagnostic Assistant

By Ishank Bhatnagar

A shop-floor diagnostic copilot for manufacturing troubleshooting that captures tacit expert
knowledge instead of just answering questions from static docs.

When the diagnostic agent is confident, it answers directly, grounded in retrieved manuals and
past incidents. When it isn't, it escalates to a human expert — and the expert's answer is
captured and written back into the knowledge base, so the next technician who hits the same
problem gets the answer instantly. The capture loop is a working model of Nonaka's SECI
tacit-to-explicit knowledge conversion framework.

## Architecture

- **Dify** (self-hosted) — agent workflow: diagnostic reasoning, confidence scoring, escalation
  branching, knowledge base (RAG)
- **MCP servers** (`mcp-servers/`) — tools the Dify agent calls:
  - `manual-rag-search` — retrieves manual sections / incident reports
  - `symptom-analysis` — reads gauge/error-code/part photos
  - `escalation-ticketing` — opens a ticket when confidence is low
  - `knowledge-ingestion` — writes an expert's answer back into the knowledge base (the SECI loop)
- **backend/** — thin FastAPI bridge: proxies the frontend's chat requests to Dify, and imports
  `ticketing.py`/`capture.py` directly (not over MCP) for the ticket list/resolve endpoints
- **frontend/** — single app, two views: technician diagnostic chat + expert escalation dashboard
- **knowledge-base/** — manuals, incident logs, and growing captured-expert-answers corpus
- **data/** — synthetic manufacturing-line dataset generator + labeled eval scenarios
- **eval/** — scores diagnostic accuracy and knowledge-base growth
- **observability/** — Langfuse trace logging (separate compose project, see STATUS.md Phase 09)

## Local development

Dify itself runs from a separate self-hosted clone (not vendored into this repo):

```
~/projects/dify-platform/docker   # official Dify docker-compose deployment
```

This repo holds the exported workflow DSL (`dify-workflow/`), the custom MCP servers, the
knowledge base source content, and everything else that is actually this project's code.

Bring up Dify:

```
cd ~/projects/dify-platform/docker
docker compose up -d
```

Then visit http://localhost to create an admin account and add Grok as a model provider.

### This repo's own services (MCP servers, backend, frontend)

Either as plain local processes (see `STATUS.md` "Steps to resume after a reboot"), or all
together via Docker Compose:

```
docker compose up -d --build
```

Frontend: http://localhost:5173 · Backend: http://localhost:8005 · MCP servers: 8001-8004
(published on the same ports either way, so Dify's `host.docker.internal:<port>/mcp`
registration doesn't need to change based on which way you run them).
