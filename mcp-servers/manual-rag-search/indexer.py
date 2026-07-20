"""Builds and queries a FAISS index over the Line 7 knowledge base:
manuals, incident logs, and (once Phase 07 exists) captured expert answers.
"""

import json
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge-base"
INDEX_DIR = Path(__file__).resolve().parent / "index"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
FAULT_ID_RE = re.compile(r"\b[A-Z]{2,5}-\d{2}\b")

_model = None
_index = None
_chunks = None
_index_mtime = None


def _index_files_mtime():
    index_path = INDEX_DIR / "kb.index"
    chunks_path = INDEX_DIR / "chunks.json"
    if not index_path.exists() or not chunks_path.exists():
        return None
    return max(index_path.stat().st_mtime, chunks_path.stat().st_mtime)


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _split_manual(path: Path):
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"\n(?=## )", text)
    chunks = []
    intro = parts[0].strip()
    if intro:
        chunks.append({"text": intro, "source_type": "manual_intro"})
    for part in parts[1:]:
        stripped = part.strip()
        if stripped:
            chunks.append({"text": stripped, "source_type": "manual_section"})
    return chunks


def _load_whole_file(path: Path, source_type: str):
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [{"text": text, "source_type": source_type}]


def _collect_chunks():
    chunks = []

    for path in sorted((KB_ROOT / "manuals").glob("*.md")):
        for c in _split_manual(path):
            c["source_file"] = path.name
            chunks.append(c)

    for path in sorted((KB_ROOT / "incident-logs").glob("*.md")):
        for c in _load_whole_file(path, "incident"):
            c["source_file"] = path.name
            chunks.append(c)

    captured_dir = KB_ROOT / "captured-expert-answers"
    if captured_dir.exists():
        for path in sorted(captured_dir.glob("*.md")):
            for c in _load_whole_file(path, "captured_expert_knowledge"):
                c["source_file"] = path.name
                chunks.append(c)

    for c in chunks:
        match = FAULT_ID_RE.search(c["text"])
        c["fault_mode_id"] = match.group(0) if match else None

    return chunks


def build_index():
    chunks = _collect_chunks()
    if not chunks:
        raise RuntimeError(f"No knowledge-base content found under {KB_ROOT}")

    model = _get_model()
    embeddings = model.encode([c["text"] for c in chunks], normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "kb.index"))
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Indexed {len(chunks)} chunks from {KB_ROOT}")
    return index, chunks


def load_index(rebuild: bool = False):
    global _index, _chunks, _index_mtime
    index_path = INDEX_DIR / "kb.index"
    chunks_path = INDEX_DIR / "chunks.json"

    if rebuild or not index_path.exists() or not chunks_path.exists():
        print("Building index...")
        _index, _chunks = build_index()
        _index_mtime = _index_files_mtime()
        return

    _index = faiss.read_index(str(index_path))
    _chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    _index_mtime = _index_files_mtime()
    print(f"Loaded index with {len(_chunks)} chunks")


def search(query: str, top_k: int = 5):
    global _index, _chunks, _index_mtime
    # Auto-reload if the on-disk index changed since we last loaded it --
    # e.g. the knowledge-ingestion server (Phase 07) rebuilt it after
    # capturing a new expert answer. Keeps this already-running server's
    # results fresh without needing a restart.
    current_mtime = _index_files_mtime()
    if _index is None or (current_mtime is not None and current_mtime != _index_mtime):
        load_index()

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype="float32")

    scores, idxs = _index.search(q_emb, top_k)
    results = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx < 0:
            continue
        chunk = _chunks[idx]
        results.append(
            {
                "text": chunk["text"],
                "source_file": chunk["source_file"],
                "source_type": chunk["source_type"],
                "fault_mode_id": chunk["fault_mode_id"],
                "score": float(score),
            }
        )
    return results
