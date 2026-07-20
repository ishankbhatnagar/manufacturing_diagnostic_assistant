from pathlib import Path

from ocr import extract_text

IMAGES_DIR = Path(__file__).resolve().parents[2] / "data" / "eval-scenarios" / "symptom-images"

for path in sorted(IMAGES_DIR.glob("*.png")):
    print(f"\n=== {path.name} ===")
    for r in extract_text(str(path)):
        print(f"  {r['confidence']:.2f}  {r['text']!r}")
