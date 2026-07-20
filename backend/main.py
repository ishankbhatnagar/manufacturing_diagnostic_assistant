"""Thin backend bridging the frontend to (1) Dify's Chat API for the
technician view and (2) the escalation-ticketing / knowledge-ingestion
MCP servers' underlying logic for the expert dashboard.

ticketing.py and capture.py are stdlib-only (no MCP protocol involved),
so they're imported directly here rather than spoken to over MCP -- see
mcp-servers/escalation-ticketing/ticketing.py and
mcp-servers/knowledge-ingestion/capture.py.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp-servers" / "escalation-ticketing"))
sys.path.insert(0, str(REPO_ROOT / "mcp-servers" / "knowledge-ingestion"))

from capture import capture_expert_answer as _capture_expert_answer  # noqa: E402
from ticketing import list_open_tickets  # noqa: E402

load_dotenv(Path(__file__).parent / ".env")

DIFY_API_BASE = os.environ.get("DIFY_API_BASE", "http://localhost/v1")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "")

CHAT_RETRIES = 5
CHAT_RETRY_BACKOFF_SECONDS = 8

app = FastAPI(title="Manufacturing Diagnostic Assistant backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/tickets")
def get_open_tickets(limit: int = 20) -> list[dict]:
    return list_open_tickets(limit=limit)


class ResolveTicketPayload(BaseModel):
    expert_answer: str
    fault_mode_id: str = ""
    expert_name: str = ""


@app.post("/api/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str, payload: ResolveTicketPayload) -> dict:
    return _capture_expert_answer(
        ticket_id=ticket_id,
        expert_answer=payload.expert_answer,
        fault_mode_id=payload.fault_mode_id,
        expert_name=payload.expert_name,
    )


async def _upload_file_to_dify(client: httpx.AsyncClient, file: UploadFile) -> str:
    resp = await client.post(
        f"{DIFY_API_BASE}/files/upload",
        headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
        files={"file": (file.filename, await file.read(), file.content_type)},
        data={"user": "technician-frontend"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


@app.post("/api/chat")
async def chat(query: str = Form(...), file: Optional[UploadFile] = File(None)) -> dict:
    if not DIFY_API_KEY:
        raise HTTPException(500, "DIFY_API_KEY is not configured on the backend")

    async with httpx.AsyncClient() as client:
        files_payload = []
        if file is not None:
            upload_id = await _upload_file_to_dify(client, file)
            files_payload = [
                {"type": "image", "transfer_method": "local_file", "upload_file_id": upload_id}
            ]

        last_error: Exception | str = "unknown error"
        for attempt in range(1, CHAT_RETRIES + 1):
            try:
                resp = await client.post(
                    f"{DIFY_API_BASE}/chat-messages",
                    headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
                    json={
                        "inputs": {},
                        "query": query,
                        "files": files_payload,
                        "response_mode": "blocking",
                        "user": "technician-frontend",
                    },
                    timeout=90,
                )
                resp.raise_for_status()
                data = resp.json()
                return {"answer": data["answer"], "conversation_id": data["conversation_id"]}
            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as e:
                last_error = e
                if attempt < CHAT_RETRIES:
                    time.sleep(CHAT_RETRY_BACKOFF_SECONDS)

        raise HTTPException(502, f"Dify chat request failed after {CHAT_RETRIES} attempts: {last_error}")
