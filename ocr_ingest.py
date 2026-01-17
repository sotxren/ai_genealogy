#!/usr/bin/env python3
"""
Single-pass OCR ingest worker.
NO daemon loop.
Called by run_all.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from schema_guard import normalize_people_name
import shutil
import hashlib
import logging
import os
import time

from ocr_engine import run_ocr
import signal

def watchdog(seconds=300):
    def handler(signum, frame):
        raise TimeoutError("Watchdog timeout exceeded")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)

# ============================================================
# PATHS (LOCAL IS SOURCE OF TRUTH)
# ============================================================
BASE = Path.home() / "genealogy"
INCOMING = BASE / "incoming"
PROCESSED = BASE / "processed"
HTML_DIR = BASE / "html"
DB_PATH = BASE / "db" / "family_tree.db"

for p in (INCOMING, PROCESSED, HTML_DIR, DB_PATH.parent):
    p.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOGGING
# ============================================================
LOG = BASE / ".ocr_ingest.log"
logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("ocr_ingest")
log.info("OCR ingest started (single pass)")

# ============================================================
# DB
# ============================================================
conn = sqlite3.connect(DB_PATH)
normalize_people_name(conn)
cursor = conn.cursor()

# ============================================================
# HASH
# ============================================================
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ============================================================
# PROCESS
# ============================================================
def process_file(path: Path, conn):
    if path.is_dir():
        return

    cursor = conn.cursor()
    file_hash = sha256(path)

    cursor.execute(
        "SELECT 1 FROM ocr_results WHERE file_hash=?",
        (file_hash,)
    )
    if cursor.fetchone():
        log.info(f"Already OCRed: {path.name}")
        return

    log.info(f"OCR start: {path.name}")

    try:
        watchdog(300)  # ⏱ 5 minute hard cap per file
        result = run_ocr(path, conn)
    except TimeoutError as e:
        log.error(f"OCR timeout: {path.name}")
        return
    except Exception as e:
        log.error(f"OCR failed: {path.name} — {e}")
        return
    finally:
        signal.alarm(0)  # 🔴 ALWAYS clear alarm

    if not result:
        log.warning(f"OCR skipped: {path.name}")
        return

    dest = PROCESSED / f"{path.stem}_{datetime.utcnow():%Y%m%d_%H%M%S}{path.suffix}"
    shutil.move(str(path), dest)

    log.info(f"Completed: {path.name}")

# ============================================================
# RUN ONCE
# ============================================================
processed_any = False

for f in sorted(INCOMING.iterdir()):
    try:
        process_file(f)
        processed_any = True
    except Exception as e:
        log.exception(f"Failed {f.name}: {e}")

conn.commit()
conn.close()

log.info("OCR ingest finished (single pass)")
