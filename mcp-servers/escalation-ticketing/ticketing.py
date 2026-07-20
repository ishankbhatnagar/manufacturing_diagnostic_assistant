"""Escalation ticket storage: one JSON file per ticket under data/tickets/."""

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

TICKETS_DIR = Path(__file__).resolve().parents[2] / "data" / "tickets"
FAULT_MODE_ID_PATTERN = re.compile(r"\b[A-Z]{2,5}-\d{2}\b")


def _new_ticket_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"TKT-{stamp}-{secrets.token_hex(2)}"


def open_ticket(symptom_report: str, ai_notes: str = "", retrieved_context: str = "") -> dict:
    """Create and persist a new escalation ticket, returning its record."""
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    ticket_id = _new_ticket_id()
    related = sorted(set(FAULT_MODE_ID_PATTERN.findall(f"{ai_notes} {retrieved_context}")))
    ticket = {
        "ticket_id": ticket_id,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "symptom_report": symptom_report,
        "ai_notes": ai_notes,
        "retrieved_context": retrieved_context,
        "related_fault_mode_ids": related,
    }
    (TICKETS_DIR / f"{ticket_id}.json").write_text(
        json.dumps(ticket, indent=2), encoding="utf-8"
    )
    return ticket


def list_open_tickets(limit: int = 20) -> list[dict]:
    """Return open tickets, most recently created first."""
    if not TICKETS_DIR.exists():
        return []
    tickets = []
    for path in TICKETS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("status") == "open":
            tickets.append(data)
    tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return tickets[:limit]
