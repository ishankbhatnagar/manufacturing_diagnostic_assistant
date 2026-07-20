"""MCP server exposing expert-answer capture into the knowledge base --
the tacit-to-explicit half of Nonaka's SECI loop.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from capture import capture_expert_answer as _capture_expert_answer

# See mcp-servers/manual-rag-search/server.py for why this is disabled:
# DNS-rebinding protection is for internet-facing servers, not a local dev
# tool reached only by our own self-hosted Dify container.
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP(
    "knowledge-ingestion", host="0.0.0.0", port=8004, transport_security=_transport_security
)


@mcp.tool()
def capture_expert_answer(
    ticket_id: str, expert_answer: str, fault_mode_id: str = "", expert_name: str = ""
) -> str:
    """Capture a human expert's answer to an escalated diagnostic ticket and
    write it into the knowledge base. This closes the tacit-to-explicit
    knowledge loop: future diagnostic queries on similar symptoms will
    retrieve this answer directly instead of escalating again.

    Args:
        ticket_id: The escalation ticket ID this answer resolves (e.g. "TKT-...").
        expert_answer: The expert's diagnosis and fix, in their own words.
        fault_mode_id: A short fault-mode code for this issue, e.g. "GBX-01".
            If the technician's issue doesn't match an existing documented
            fault mode, invent a new short id (2-5 uppercase letters, a dash,
            2 digits) so future occurrences of this exact issue get matched
            directly by search. Leave blank to let it scan expert_answer for
            an existing fault-mode-shaped code instead.
        expert_name: Who answered (optional, for attribution).
    """
    result = _capture_expert_answer(ticket_id, expert_answer, fault_mode_id, expert_name)

    message = f"Captured expert answer to {ticket_id} as {Path(result['file']).name}"
    if result["fault_mode_id"]:
        message += f" (fault mode {result['fault_mode_id']})"
    message += "."
    if result["reindexed"]:
        message += " Knowledge base index rebuilt -- this answer is now searchable immediately."
    else:
        message += (
            " WARNING: index rebuild failed, this answer is saved but not yet searchable "
            f"until re-indexed manually. Details: {result['reindex_output'][-500:]}"
        )
    if not result["ticket_found"]:
        message += f" NOTE: ticket {ticket_id} was not found, so it could not be marked resolved."
    else:
        message += f" Ticket {ticket_id} marked resolved."

    return message


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
