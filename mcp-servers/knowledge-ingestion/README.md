# knowledge-ingestion

MCP server exposing one tool, `capture_expert_answer`, which structures a
human expert's answer to an escalated ticket, writes it as a new markdown
file into `knowledge-base/captured-expert-answers/`, rebuilds the
`manual-rag-search` FAISS index, and marks the originating ticket resolved.

This is the tacit-to-explicit half of Nonaka's SECI loop -- once captured,
the next occurrence of a similar symptom gets answered directly by the
diagnostic agent instead of escalating again.

The written markdown matches the format `manual-rag-search/indexer.py`
already expects for this folder (loaded whole, `source_type:
captured_expert_knowledge`) -- it extracts a `fault_mode_id` via regex
`[A-Z]{2,5}-\d{2}`, so the file just needs that code mentioned somewhere
in the body (the header line covers it).

Reindexing reuses `manual-rag-search`'s own venv (`subprocess.run(...
.venv/Scripts/python.exe build_index.py`) rather than duplicating
`faiss`/`sentence-transformers` here. The already-running `manual-rag-search`
server picks up the change on its very next search call -- `indexer.py`'s
`search()` checks the on-disk index files' mtime and auto-reloads if they
changed, so no restart is needed for new knowledge to become searchable.

## Setup

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Requires `manual-rag-search`'s own venv to already be set up (for
reindexing) -- see `mcp-servers/manual-rag-search/README.md`.

## Run

```
.venv\Scripts\python.exe server.py
```

Serves streamable-HTTP MCP at `http://localhost:8004/mcp`.

## Register in Dify

**Tools -> MCP -> Add MCP Server**, URL `http://host.docker.internal:8004/mcp`,
name `knowledge-ingestion`. (The SSRF-proxy allowlist added in Phase 02 already
covers `host.docker.internal` for any port, so no further proxy config is
needed.)
