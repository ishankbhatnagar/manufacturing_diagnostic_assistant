"""Generates synthetic panel/display photos for fault modes that have a
legible on-equipment readout (error code display, HMI banner, indicator
light text). Not every fault mode gets an image -- only ones where a real
technician would actually photograph a screen or panel.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parents[1] / "eval-scenarios" / "symptom-images"

FONT_CANDIDATES = [
    "C:/Windows/Fonts/consolab.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

IMAGES = [
    {
        "filename": "vfd01_display.png",
        "fault_mode_id": "VFD-01",
        "bg": (15, 15, 20),
        "fg": (255, 60, 40),
        "lines": ["E003", "OVERCURRENT"],
    },
    {
        "filename": "mtr01_display.png",
        "fault_mode_id": "MTR-01",
        "bg": (10, 10, 10),
        "fg": (255, 140, 0),
        "lines": ["OL TRIP", "MOTOR THERMAL"],
    },
    {
        "filename": "plc01_hmi.png",
        "fault_mode_id": "PLC-01",
        "bg": (20, 20, 30),
        "fg": (255, 40, 40),
        "lines": ["COMM FAULT", "PLC LINK LOST"],
    },
    {
        "filename": "elec01_display.png",
        "fault_mode_id": "ELEC-01",
        "bg": (12, 12, 12),
        "fg": (255, 200, 0),
        "lines": ["UNDER VOLTAGE", "SUPPLY SAG"],
    },
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_image(spec: dict) -> Image.Image:
    w, h = 640, 360
    img = Image.new("RGB", (w, h), spec["bg"])
    draw = ImageDraw.Draw(img)

    # panel bezel
    draw.rectangle([10, 10, w - 10, h - 10], outline=(80, 80, 80), width=6)

    big_font = _load_font(72)
    small_font = _load_font(28)

    line1, line2 = spec["lines"][0], spec["lines"][1] if len(spec["lines"]) > 1 else ""

    bbox1 = draw.textbbox((0, 0), line1, font=big_font)
    x1 = (w - (bbox1[2] - bbox1[0])) / 2
    draw.text((x1, 110), line1, font=big_font, fill=spec["fg"])

    if line2:
        bbox2 = draw.textbbox((0, 0), line2, font=small_font)
        x2 = (w - (bbox2[2] - bbox2[0])) / 2
        draw.text((x2, 220), line2, font=small_font, fill=spec["fg"])

    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for spec in IMAGES:
        img = render_image(spec)
        path = OUT_DIR / spec["filename"]
        img.save(path)
        manifest.append(
            {
                "filename": spec["filename"],
                "fault_mode_id": spec["fault_mode_id"],
                "expected_text_contains": spec["lines"],
            }
        )
        print(f"Wrote {path}")

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest with {len(manifest)} entries")


if __name__ == "__main__":
    main()
