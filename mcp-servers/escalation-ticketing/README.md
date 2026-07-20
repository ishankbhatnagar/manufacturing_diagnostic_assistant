# escalation-ticketing

MCP server exposing two tools for the diagnostic agent's escalation path:

- `open_escalation_ticket` -- opens a ticket when the agent can't confidently
  answer, storing the technician's symptom report, the agent's notes, and the
  retrieved context it considered. Scans that text for `fault_mode_id`-shaped
  tokens (e.g. `VFD-01`) and records any it finds as `related_fault_mode_ids`,
  even though by definition none matched confidently enough to answer.
- `list_open_escalation_tickets` -- lists open tickets, most recent first.

Tickets are stored as one JSON file per ticket under `data/tickets/`. No
dashboard yet (Phase 10) -- this is just the storage + tool layer.

## Setup

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```
.venv\Scripts\python.exe server.py
```

Serves streamable-HTTP MCP at `http://localhost:8003/mcp`.

## Register in Dify

**Tools -> MCP -> Add MCP Server**, URL `http://host.docker.internal:8003/mcp`,
name `escalation-ticketing`. (The SSRF-proxy allowlist added in Phase 02 already
covers `host.docker.internal` for any port, so no further proxy config is
needed.)
