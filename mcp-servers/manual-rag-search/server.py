"""MCP server exposing semantic search over the Line 7 knowledge base."""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from indexer import load_index, search

# The MCP SDK's DNS-rebinding protection (Host/Origin header allowlisting)
# defends internet-facing servers against malicious browser pages -- not the
# threat model for a server that only ever runs on localhost for local dev
# and is called by our own self-hosted Dify container. Disabling it avoids
# guessing Dify's exact outbound Origin header; re-enable with a real
# allowlist before ever exposing this server beyond localhost.
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP("manual-rag-search", host="0.0.0.0", port=8001, transport_security=_transport_security)


@mcp.tool()
def search_manuals_and_incidents(query: str, top_k: int = 5) -> str:
    """Search Line 7 equipment manuals, past incident logs, and captured expert
    knowledge for passages relevant to a reported symptom or fault. Use this
    before proposing a diagnosis -- ground your answer in what it returns.

    Args:
        query: The technician's symptom description, or a specific fault/error code.
        top_k: Number of passages to return (default 5).
    """
    results = search(query, top_k=top_k)
    if not results:
        return "No relevant passages found in manuals, incident logs, or captured expert knowledge."

    blocks = []
    for r in results:
        header = f"[{r['source_type']}] {r['source_file']}"
        if r["fault_mode_id"]:
            header += f" (fault mode: {r['fault_mode_id']})"
        header += f" -- relevance {r['score']:.2f}"
        blocks.append(f"{header}\n{r['text']}")
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    load_index()
    mcp.run(transport="streamable-http")
