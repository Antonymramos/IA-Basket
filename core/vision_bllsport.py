from __future__ import annotations

import base64
import io
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class VisionResult:
    ok: bool
    placar: dict[str, int] | None
    tempo_video: str | None
    raw_text: str
    error: str | None = None


def _try_import_pillow():
    try:
        from PIL import Image  # type: ignore

        return Image
    except Exception:
        return None


def _try_import_cv2():
    try:
        import cv2  # type: ignore

        return cv2
    except Exception:
        return None


def _try_import_pytesseract():
    try:
        import pytesseract  # type: ignore

        return pytesseract
    except Exception:
        return None


def decode_base64_image(frame_base64: str):
    """Decodifica base64 (data URI ou puro) em PIL Image."""
    Image = _try_import_pillow()
    if Image is None:
        raise RuntimeError("Dependência ausente: Pillow. Instale: pip install pillow")

    b64 = frame_base64.strip()
    if "," in b64 and b64.lower().startswith("data:"):
        b64 = b64.split(",", 1)[1]

    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert("RGB")


def crop_image_pil(image, crop: dict[str, int] | None):
    if not crop:
        return image

    x = int(crop.get("x", 0))
    y = int(crop.get("y", 0))
    w = int(crop.get("w", 0))
    h = int(crop.get("h", 0))

    if w <= 0 or h <= 0:
        return image

    return image.crop((x, y, x + w, y + h))


def ocr_text_from_image(image) -> str:
    """OCR básico. Usa OpenCV se disponível, senão Pillow direto."""
    pytesseract = _try_import_pytesseract()
    if pytesseract is None:
        raise RuntimeError(
            "Dependência ausente: pytesseract. Instale: pip install pytesseract e instale o Tesseract no Windows."
        )

    cv2 = _try_import_cv2()
    if cv2 is None:
        # OCR direto
        return pytesseract.image_to_string(image, lang="eng")

    import numpy as np  # type: ignore

    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return pytesseract.image_to_string(th, lang="eng")


def parse_score_and_clock(text: str) -> tuple[dict[str, int] | None, str | None]:
    """Extrai placar e tempo do texto OCR (heurístico)."""
    if not text:
        return None, None

    normalized = " ".join(text.split())

    # Score: 93-85 / 93:85
    m = re.search(r"\b(\d{1,3})\s*[-:]\s*(\d{1,3})\b", normalized)
    score = None
    if m:
        try:
            h = int(m.group(1))
            a = int(m.group(2))
            if 0 <= h <= 250 and 0 <= a <= 250:
                score = {"Home": h, "Away": a}
        except Exception:
            score = None

    # Clock: Q1 05:03 or Q 1 05:03
    t = None
    tm = re.search(r"\bQ\s*(\d)\s*(\d{1,2}):(\d{2})\b", normalized, flags=re.IGNORECASE)
    if tm:
        q = tm.group(1)
        mm = tm.group(2)
        ss = tm.group(3)
        t = f"Q{q} {mm}:{ss}"

    return score, t


def analyze_bllsport_frame(frame_base64: str, crop: dict[str, int] | None = None) -> VisionResult:
    """Pipeline OCR: base64 -> (crop) -> OCR -> parse placar/tempo."""
    try:
        img = decode_base64_image(frame_base64)
        img = crop_image_pil(img, crop)
        text = ocr_text_from_image(img)
        placar, tempo = parse_score_and_clock(text)
        ok = bool(placar or tempo)
        return VisionResult(ok=ok, placar=placar, tempo_video=tempo, raw_text=text)
    except Exception as exc:
        return VisionResult(ok=False, placar=None, tempo_video=None, raw_text="", error=str(exc))
