"""CLI: (re)build the FAISS index from the current knowledge-base contents.

Run this once initially, and again any time knowledge-base/ changes --
including after the knowledge-ingestion MCP server (Phase 07) writes a new
captured expert answer.
"""

from indexer import build_index

if __name__ == "__main__":
    build_index()
