# manual-rag-search

MCP server exposing one tool, `search_manuals_and_incidents`, backed by a local
FAISS index over `knowledge-base/manuals/`, `knowledge-base/incident-logs/`,
and `knowledge-base/captured-expert-answers/`.

Embeddings are computed locally with `paraphrase-multilingual-MiniLM-L12-v2`
(sentence-transformers) -- no external API key required.

## Setup

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe build_index.py
```

Re-run `build_index.py` any time the knowledge base changes (including after
the knowledge-ingestion server writes a new captured expert answer).

## Run

```
.venv\Scripts\python.exe server.py
```

Serves streamable-HTTP MCP at `http://localhost:8001/mcp`.

## Register in Dify

Dify runs in Docker, so it can't reach `localhost` on the host machine --
use `http://host.docker.internal:8001/mcp` instead.

In Dify Studio: **Tools -> MCP -> Add MCP Server**, paste that URL, give it a
name (`manual-rag-search`), save. The `search_manuals_and_incidents` tool
should appear and can be attached to an agent/workflow node.
