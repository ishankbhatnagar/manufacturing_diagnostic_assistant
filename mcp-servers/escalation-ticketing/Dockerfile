FROM python:3.12-slim

WORKDIR /app

COPY mcp-servers/escalation-ticketing/requirements.txt mcp-servers/escalation-ticketing/
RUN pip install --no-cache-dir -r mcp-servers/escalation-ticketing/requirements.txt

COPY mcp-servers/escalation-ticketing/ mcp-servers/escalation-ticketing/

WORKDIR /app/mcp-servers/escalation-ticketing
EXPOSE 8003
CMD ["python", "server.py"]
