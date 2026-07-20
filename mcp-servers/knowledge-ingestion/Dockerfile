FROM python:3.12-slim

WORKDIR /app

# Also installs manual-rag-search's (heavier) deps: capture.py shells out to
# manual-rag-search/build_index.py to reindex after every capture, and in a
# container there's no sibling venv to reuse (see capture.py's fallback to
# sys.executable) -- so this container needs those deps itself.
COPY mcp-servers/knowledge-ingestion/requirements.txt mcp-servers/knowledge-ingestion/
COPY mcp-servers/manual-rag-search/requirements.txt mcp-servers/manual-rag-search/
RUN pip install --no-cache-dir \
    -r mcp-servers/knowledge-ingestion/requirements.txt \
    -r mcp-servers/manual-rag-search/requirements.txt

COPY mcp-servers/knowledge-ingestion/ mcp-servers/knowledge-ingestion/
COPY mcp-servers/manual-rag-search/*.py mcp-servers/manual-rag-search/
# Baked in for consistent seeding of the shared knowledge_base named volume
# regardless of which service (this one or manual-rag-search) first mounts
# it -- see the matching comment in manual-rag-search/Dockerfile.
COPY knowledge-base/ knowledge-base/

WORKDIR /app/mcp-servers/knowledge-ingestion
EXPOSE 8004
CMD ["python", "server.py"]
