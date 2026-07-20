FROM python:3.12-slim

WORKDIR /app

COPY mcp-servers/manual-rag-search/requirements.txt mcp-servers/manual-rag-search/
RUN pip install --no-cache-dir -r mcp-servers/manual-rag-search/requirements.txt

COPY mcp-servers/manual-rag-search/ mcp-servers/manual-rag-search/
# Baked in so the knowledge_base named volume seeds correctly from this on
# first run (Docker copies an image's existing content into a fresh empty
# named volume mounted at the same path) -- captured-expert-answers/ then
# grows at runtime on top of this baseline.
COPY knowledge-base/ knowledge-base/

WORKDIR /app/mcp-servers/manual-rag-search
RUN chmod +x entrypoint.sh
EXPOSE 8001
CMD ["./entrypoint.sh"]
