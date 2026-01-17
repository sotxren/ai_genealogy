#!/usr/bin/env python3

from dataclasses import dataclass

# ============================================================
# Data class for OCR results
# ============================================================
@dataclass
class OCRResult:
    text: str
    engine: str
    confidence: float

# ============================================================
# Evaluation logic
# ============================================================
def evaluate(result: OCRResult) -> dict:
    """
    Simple evaluator: marks low-confidence OCR as needs_review.
    """
    threshold = 0.55
    needs_review = result.confidence < threshold
    # Optionally, boost confidence for TrOCR or EasyOCR heuristics here
    confidence = min(result.confidence + 0.1, 1.0) if not needs_review else result.confidence
    return {"confidence": confidence, "needs_review": needs_review}
