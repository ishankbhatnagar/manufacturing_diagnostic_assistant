# symptom-analysis

MCP server exposing one tool, `analyze_symptom_image`, which runs OCR
(EasyOCR) over a photo of an equipment panel, digital display, HMI screen,
or error-code plate and returns the detected text.

## Setup

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```
.venv\Scripts\python.exe server.py
```

Serves streamable-HTTP MCP at `http://localhost:8002/mcp`.

## Register in Dify

**Tools -> MCP -> Add MCP Server**, URL `http://host.docker.internal:8002/mcp`,
name `symptom-analysis`. (The SSRF-proxy allowlist added in Phase 02 already
covers `host.docker.internal` for any port, so no further proxy config is
needed.)
