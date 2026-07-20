FROM python:3.12-slim

WORKDIR /app

# ticketing.py and capture.py are imported directly (see main.py) rather than
# spoken to over MCP. capture.py's reindex step in turn shells out to
# manual-rag-search/build_index.py, so this image needs that server's code
# and (heavier) deps too -- same reasoning as knowledge-ingestion/Dockerfile.
COPY backend/requirements.txt backend/
COPY mcp-servers/manual-rag-search/requirements.txt mcp-servers/manual-rag-search/
RUN pip install --no-cache-dir \
    -r backend/requirements.txt \
    -r mcp-servers/manual-rag-search/requirements.txt

COPY backend/ backend/
COPY mcp-servers/escalation-ticketing/ticketing.py mcp-servers/escalation-ticketing/
COPY mcp-servers/knowledge-ingestion/capture.py mcp-servers/knowledge-ingestion/
COPY mcp-servers/manual-rag-search/*.py mcp-servers/manual-rag-search/
# Baked in for consistent seeding of the shared knowledge_base named volume
# regardless of which service first mounts it -- see the matching comment in
# manual-rag-search/Dockerfile.
COPY knowledge-base/ knowledge-base/

WORKDIR /app/backend
EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
