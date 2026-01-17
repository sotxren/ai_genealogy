#!/usr/bin/env python3
"""
OCR confidence evaluation & retry policy
"""

from dataclasses import dataclass

MIN_CONFIDENCE = 0.55
GOOD_CONFIDENCE = 0.75

@dataclass
class OCRResult:
    text: str
    engine: str
    confidence: float

def normalize(engine: str, confidence: float) -> float:
    engine = engine.lower()

    if engine == "easyocr":
        return confidence
    if engine == "trocr":
        return min(confidence, 0.85)
    if engine == "text":
        return 1.0 if confidence > 0 else 0.0

    return confidence * 0.5

def evaluate(result: OCRResult) -> dict:
    norm = normalize(result.engine, result.confidence)

    return {
        "confidence": norm,
        "accepted": norm >= MIN_CONFIDENCE,
        "needs_review": norm < MIN_CONFIDENCE,
        "quality": (
            "good" if norm >= GOOD_CONFIDENCE
            else "ok" if norm >= MIN_CONFIDENCE
            else "poor"
        )
    }
