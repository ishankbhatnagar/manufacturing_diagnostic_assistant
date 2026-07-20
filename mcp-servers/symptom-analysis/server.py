"""MCP server exposing OCR-based analysis of equipment panel/display photos."""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from ocr import extract_text

# See mcp-servers/manual-rag-search/server.py for why this is disabled:
# DNS-rebinding protection is for internet-facing servers, not a local dev
# tool reached only by our own self-hosted Dify container.
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP("symptom-analysis", host="0.0.0.0", port=8002, transport_security=_transport_security)


@mcp.tool()
def analyze_symptom_image(image: str) -> str:
    """Read text from a photo of an equipment panel, digital display, HMI
    screen, or error-code plate. Accepts a local file path or a base64 /
    data-URI encoded image. Use this when a technician submits a photo
    alongside a symptom report -- pass any extracted error codes into the
    manual/incident search tool to ground the diagnosis.

    Args:
        image: File path or base64-encoded image data.
    """
    try:
        results = extract_text(image)
    except ValueError as e:
        return f"Could not read image: {e}"

    if not results:
        return "No legible text found in the image."

    lines = [f'"{r["text"]}" (confidence {r["confidence"]})' for r in results]
    return "Text detected in image, highest confidence first:\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
