from indexer import search

queries = [
    "motor keeps overheating and tripping after running a while",
    "there's a high whine near the tail pulley, no error codes though",
    "getting E003 on the drive at startup",
]

for q in queries:
    print(f"\n=== Query: {q!r} ===")
    for r in search(q, top_k=3):
        print(f"  score={r['score']:.3f} [{r['source_type']}] {r['source_file']} fault={r['fault_mode_id']}")
        print(f"    {r['text'][:100]!r}...")
