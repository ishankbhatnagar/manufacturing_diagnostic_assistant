FROM python:3.12-slim

# EasyOCR pulls in opencv, which needs these at runtime even though the
# base slim image doesn't ship them.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY mcp-servers/symptom-analysis/requirements.txt mcp-servers/symptom-analysis/
RUN pip install --no-cache-dir -r mcp-servers/symptom-analysis/requirements.txt

COPY mcp-servers/symptom-analysis/ mcp-servers/symptom-analysis/

WORKDIR /app/mcp-servers/symptom-analysis
ENV PYTHONIOENCODING=utf-8
EXPOSE 8002
CMD ["python", "server.py"]
