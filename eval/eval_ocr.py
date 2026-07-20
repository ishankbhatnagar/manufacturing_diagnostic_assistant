"""OCR accuracy check against data/eval-scenarios/symptom-images/manifest.json.

Unlike run_scenarios.py, this doesn't need Dify/Docker/Groq -- just the
symptom-analysis OCR module -- so it's safe to run in CI.

Usage:
    cd mcp-servers/symptom-analysis && .venv\\Scripts\\python.exe ../../eval/eval_ocr.py
(needs to run with symptom-analysis's venv/deps -- see eval/README.md)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "eval-scenarios" / "symptom-images" / "manifest.json"
IMAGES_DIR = MANIFEST_PATH.parent

sys.path.insert(0, str(REPO_ROOT / "mcp-servers" / "symptom-analysis"))
from ocr import extract_text  # noqa: E402


def _words_present(phrase: str, detected_text: str) -> bool:
    """Checks each word of `phrase` appears somewhere in `detected_text`,
    order-independent. EasyOCR detects each on-screen text region as a
    separate result, so a multi-word expected phrase (e.g. "OL TRIP") can
    legitimately come back as separate regions in a different order (e.g.
    "TRIP" then "OL") -- that's still a correct read. What actually matters
    downstream is that these words end up in the text handed to the
    embedding-based search query, where word order doesn't affect matching;
    a strict contiguous-substring check would fail on correct OCR output.
    """
    return all(word in detected_text for word in phrase.upper().split())


def run() -> bool:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_passed = True

    for entry in manifest:
        image_path = IMAGES_DIR / entry["filename"]
        results = extract_text(str(image_path))
        detected_text = " ".join(r["text"].upper() for r in results)

        missing = [
            expected
            for expected in entry["expected_text_contains"]
            if not _words_present(expected, detected_text)
        ]

        status = "PASS" if not missing else "FAIL"
        if missing:
            all_passed = False
        print(f"[{status}] {entry['filename']} (fault mode {entry['fault_mode_id']})")
        print(f"       detected: {detected_text!r}")
        if missing:
            print(f"       missing:  {missing}")

    return all_passed


if __name__ == "__main__":
    ok = run()
    print("\nAll OCR checks passed." if ok else "\nSome OCR checks FAILED.")
    sys.exit(0 if ok else 1)
