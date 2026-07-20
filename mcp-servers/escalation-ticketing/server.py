"""MCP server exposing escalation ticketing for the diagnostic agent."""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from ticketing import list_open_tickets, open_ticket

# See mcp-servers/manual-rag-search/server.py for why this is disabled:
# DNS-rebinding protection is for internet-facing servers, not a local dev
# tool reached only by our own self-hosted Dify container.
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP(
    "escalation-ticketing", host="0.0.0.0", port=8003, transport_security=_transport_security
)


@mcp.tool()
def open_escalation_ticket(symptom_report: str, ai_notes: str = "", retrieved_context: str = "") -> str:
    """Open an escalation ticket for a symptom you could not confidently
    diagnose, routing it to a human expert. Call this whenever you decide to
    escalate rather than answer directly.

    Args:
        symptom_report: The technician's original reported symptom, verbatim.
        ai_notes: What you found so far and why you're escalating (optional).
        retrieved_context: The raw manual/incident-log passages you considered,
            so the expert has the same information you did (optional).
    """
    ticket = open_ticket(symptom_report, ai_notes, retrieved_context)
    related = ", ".join(ticket["related_fault_mode_ids"]) or "none"
    return (
        f"Ticket {ticket['ticket_id']} opened and routed to a human expert.\n"
        f"Related fault mode IDs mentioned in context: {related}"
    )


@mcp.tool()
def list_open_escalation_tickets(limit: int = 20) -> str:
    """List currently open escalation tickets, most recently created first.
    Useful for checking on outstanding cases awaiting expert review.

    Args:
        limit: Maximum number of tickets to return (default 20).
    """
    tickets = list_open_tickets(limit=limit)
    if not tickets:
        return "No open tickets."

    blocks = []
    for t in tickets:
        related = ", ".join(t["related_fault_mode_ids"]) or "none"
        blocks.append(
            f"[{t['ticket_id']}] {t['created_at']}\n"
            f"Symptom: {t['symptom_report']}\n"
            f"Related fault modes: {related}"
        )
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
