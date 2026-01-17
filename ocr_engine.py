#!/usr/bin/env python3
"""
OCR Engine
- EasyOCR primary
- TrOCR fallback (offline, local)
- OMV is backup only; models never loaded from network share
"""

# ============================================================
# OFFLINE + LOCAL MODEL CONFIG (MUST BE FIRST)
# ============================================================
import os
from pathlib import Path

BASE = Path.home() / "genealogy"
LOCAL_MODEL_DIR = BASE / "models"  # local offline model cache

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HOME"] = str(LOCAL_MODEL_DIR)

# ============================================================
# STANDARD LIBS
# ============================================================
from datetime import datetime
import hashlib
import logging
import sqlite3

# ============================================================
# THIRD PARTY
# ============================================================
import numpy as np
import torch
from PIL import Image
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# ============================================================
# INTERNAL MODULES
# ============================================================
from preprocess import preprocess_image
from confidence_engine import OCRResult, evaluate

# ============================================================
# PATHS + DB
# ============================================================
DB_PATH = BASE / "db/family_tree.db"
MODEL_ID = "microsoft/trocr-base-handwritten"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    filename=BASE / ".genealogy_ocr.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ocr_engine")
log.info("OCR engine starting")
log.info(f"DEVICE={DEVICE}")
log.info(f"Local HF_HOME={LOCAL_MODEL_DIR}")

# ============================================================
# OCR ENGINES (INITIALIZED ONCE)
# ============================================================

# EasyOCR primary
easyocr_reader = easyocr.Reader(["en"], gpu=False)

# TrOCR fallback (offline, local)
trocr_processor = None
trocr_model = None
try:
    trocr_processor = TrOCRProcessor.from_pretrained(MODEL_ID)
    trocr_model = VisionEncoderDecoderModel.from_pretrained(MODEL_ID)
    trocr_model.to(DEVICE)
    trocr_model.eval()
    log.info("TrOCR loaded successfully (offline, local)")
except Exception as e:
    log.warning(f"TrOCR could not load offline: {e}")

# ============================================================
# UTILS
# ============================================================
def hash_file(path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def get_confidence(scores):
    """Simple confidence estimation for EasyOCR."""
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


# ============================================================
# CORE OCR FUNCTION
# ============================================================
def run_ocr(file_path: Path, conn: sqlite3.Connection, confidence_threshold=0.5):
    """
    Preprocess image → OCR → confidence evaluation → store result.
    Returns: dict {text, engine, confidence, needs_review}
    """
    cursor = conn.cursor()
    file_hash = hash_file(file_path)

    # Check if already processed
    cursor.execute("SELECT id FROM ocr_results WHERE file_hash=?", (file_hash,))
    if cursor.fetchone():
        log.info(f"OCR already exists for {file_path.name}")
        return None

    log.info(f"Processing {file_path.name}")

    img = None
    text = ""

    # ------------------------------------------------------------
    # PREPROCESS
    # ------------------------------------------------------------
    if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        img = preprocess_image(file_path)
    else:
        try:
            text = file_path.read_text(errors="ignore")
        except Exception:
            text = ""

    # ------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------
    ocr_text = ""
    engine_used = ""
    confidence = 0.0
    needs_review = False

    # IMAGE OCR
    if img is not None:
        # EasyOCR first
        easy_results = easyocr_reader.readtext(np.array(img), detail=1)
        ocr_text = "\n".join([t[1] for t in easy_results])
        confidence = get_confidence([t[2] for t in easy_results])
        engine_used = "easyocr"

        # Retry with TrOCR if confidence low and TrOCR loaded
        if confidence < confidence_threshold and trocr_processor and trocr_model:
            try:
                trocr_inputs = trocr_processor(images=img, return_tensors="pt").to(DEVICE)
                output_ids = trocr_model.generate(**trocr_inputs)
                ocr_text = trocr_processor.batch_decode(
                    output_ids, skip_special_tokens=True
                )[0]
                confidence = 0.75  # heuristic
                engine_used = "trocr"
            except Exception as e:
                log.warning(f"TrOCR retry failed for {file_path.name}: {e}")

        # --------------------------------------------------------
        # CONFIDENCE ENGINE DELEGATION
        # --------------------------------------------------------
        decision = evaluate(
            OCRResult(
                text=ocr_text,
                engine=engine_used,
                confidence=confidence
            )
        )
        confidence = decision["confidence"]
        needs_review = decision["needs_review"]

    # NON-IMAGE FILES
    else:
        ocr_text = text
        engine_used = "text"
        confidence = 1.0 if text.strip() else 0.0
        needs_review = not bool(text.strip())

    # ------------------------------------------------------------
    # SAVE TO DB
    # ------------------------------------------------------------
    cursor.execute(
        """
        INSERT INTO ocr_results
        (file_hash, file_path, engine, confidence, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            file_hash,
            str(file_path),
            engine_used,
            confidence,
            ocr_text,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()

    log.info(
        f"OCR complete for {file_path.name} | "
        f"Engine: {engine_used} | "
        f"Confidence: {confidence:.2f} | "
        f"Needs review: {needs_review}"
    )

    return {
        "text": ocr_text,
        "engine": engine_used,
        "confidence": confidence,
        "needs_review": needs_review
    }
