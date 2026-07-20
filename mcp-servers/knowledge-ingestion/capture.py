"""Captures a human expert's answer to an escalated ticket into the
knowledge base, and marks the originating ticket resolved. This is the
tacit-to-explicit half of the SECI loop: once captured, the next occurrence
of a similar symptom is retrieved directly instead of escalating again.
"""

import sys
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_CAPTURED_DIR = REPO_ROOT / "knowledge-base" / "captured-expert-answers"
TICKETS_DIR = REPO_ROOT / "data" / "tickets"
MANUAL_RAG_DIR = REPO_ROOT / "mcp-servers" / "manual-rag-search"
MANUAL_RAG_VENV_PYTHON = MANUAL_RAG_DIR / ".venv" / "Scripts" / "python.exe"

FAULT_MODE_ID_PATTERN = re.compile(r"\b[A-Z]{2,5}-\d{2}\b")


def _rebuild_search_index() -> tuple[bool, str]:
    """Reruns manual-rag-search's own build_index.py. In local dev, reuses its
    venv (which already has faiss/sentence-transformers) rather than
    duplicating those heavy dependencies here. In a container, there's no
    sibling venv -- manual-rag-search's deps are installed in this
    container's own environment instead (see mcp-servers/knowledge-ingestion/
    Dockerfile), so fall back to the current interpreter. Either way, the
    already-running manual-rag-search server picks up the change on its next
    search call via indexer.py's mtime check.
    """
    python = str(MANUAL_RAG_VENV_PYTHON) if MANUAL_RAG_VENV_PYTHON.exists() else sys.executable
    result = subprocess.run(
        [python, "build_index.py"],
        cwd=str(MANUAL_RAG_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0, (result.stdout + result.stderr)


def capture_expert_answer(
    ticket_id: str, expert_answer: str, fault_mode_id: str = "", expert_name: str = ""
) -> dict:
    ticket_path = TICKETS_DIR / f"{ticket_id}.json"
    ticket = json.loads(ticket_path.read_text(encoding="utf-8")) if ticket_path.exists() else None
    symptom_report = ticket["symptom_report"] if ticket else ""

    resolved_fault_mode_id = fault_mode_id.strip() or None
    if not resolved_fault_mode_id:
        match = FAULT_MODE_ID_PATTERN.search(expert_answer)
        resolved_fault_mode_id = match.group(0) if match else None

    now = datetime.now(timezone.utc)
    slug = (resolved_fault_mode_id or ticket_id).lower().replace(" ", "-")
    filename = f"{slug}-{now.strftime('%Y%m%d%H%M%S')}.md"

    lines = [f"# Captured expert answer -- {resolved_fault_mode_id or '(unclassified)'}", ""]
    lines.append(f"- **Ticket:** {ticket_id}")
    lines.append(f"- **Captured:** {now.isoformat()}")
    if expert_name:
        lines.append(f"- **Answered by:** {expert_name}")
    if resolved_fault_mode_id:
        lines.append(f"- **Related fault mode:** {resolved_fault_mode_id}")
    lines.append("")
    if symptom_report:
        lines.append("## Reported symptom")
        lines.append("")
        lines.append(f"> {symptom_report}")
        lines.append("")
    lines.append("## Expert answer")
    lines.append("")
    lines.append(expert_answer)
    lines.append("")

    KB_CAPTURED_DIR.mkdir(parents=True, exist_ok=True)
    md_path = KB_CAPTURED_DIR / filename
    md_path.write_text("\n".join(lines), encoding="utf-8")

    reindexed, reindex_output = _rebuild_search_index()

    if ticket_path.exists():
        ticket["status"] = "resolved"
        ticket["resolved_at"] = now.isoformat()
        ticket["expert_answer"] = expert_answer
        ticket["expert_name"] = expert_name
        ticket["captured_fault_mode_id"] = resolved_fault_mode_id
        ticket_path.write_text(json.dumps(ticket, indent=2), encoding="utf-8")

    return {
        "file": str(md_path),
        "fault_mode_id": resolved_fault_mode_id,
        "reindexed": reindexed,
        "reindex_output": reindex_output,
        "ticket_found": ticket is not None,
    }
