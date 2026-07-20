"""OCR extraction for equipment panel/display photos using EasyOCR."""

import base64
import binascii
import io
import tempfile
import urllib.request
from pathlib import Path

import easyocr
from PIL import Image

_reader: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def _resolve_image_path(image: str) -> Path:
    """Accept a filesystem path, an http(s) URL, or a base64 / data-URI
    encoded image, and return a local file path EasyOCR can read.
    """
    path = Path(image)
    if path.exists():
        return path

    if image.startswith("http://") or image.startswith("https://"):
        with urllib.request.urlopen(image, timeout=15) as resp:
            image_bytes = resp.read()
        img = Image.open(io.BytesIO(image_bytes))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        return Path(tmp.name)

    raw = image
    if raw.startswith("data:image"):
        raw = raw.split(",", 1)[-1]

    try:
        image_bytes = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError(
            f"'{image}' is neither an existing file path nor valid base64 image data"
        ) from e

    img = Image.open(io.BytesIO(image_bytes))
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return Path(tmp.name)


def extract_text(image: str, min_confidence: float = 0.4) -> list[dict]:
    """Run OCR on an image (file path or base64 string).

    Returns a list of {"text": str, "confidence": float}, sorted by
    confidence descending, filtered to results above min_confidence.
    """
    image_path = _resolve_image_path(image)
    reader = _get_reader()
    raw_results = reader.readtext(str(image_path))

    results = [
        {"text": text.strip(), "confidence": round(float(confidence), 3)}
        for _bbox, text, confidence in raw_results
        if confidence >= min_confidence and text.strip()
    ]
    results.sort(key=lambda r: r["confidence"], reverse=True)
    return results
