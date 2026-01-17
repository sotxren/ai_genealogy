#!/usr/bin/env python3
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# ============================================================
# PATHS + LOGGING
# ============================================================
BASE = Path.home() / "genealogy"
DB_PATH = BASE / "db/family_tree.db"

logging.basicConfig(
    filename=BASE / ".genealogy_timelines.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("timelines")
log.info("Timeline builder initialized")

# ============================================================
# DATABASE CONNECTION
# ============================================================
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ============================================================
# ENSURE EVENTS TABLE EXISTS
# ============================================================
c.execute("""
CREATE TABLE IF NOT EXISTS person_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    event_type TEXT,
    event_date TEXT,
    description TEXT,
    source_file TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id)
)
""")
conn.commit()

# ============================================================
# HELPER: PARSE DATES
# ============================================================
def parse_date(date_str: str) -> str:
    """
    Normalize dates to ISO format. If invalid, return empty string.
    """
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except Exception:
            continue
    return ""

# ============================================================
# BUILD TIMELINES
# ============================================================
c.execute("SELECT id, name FROM people")
people = c.fetchall()

log.info(f"Processing timelines for {len(people)} people")

for person_id, name in people:
    # Fetch all files linked to this person
    c.execute("""
        SELECT f.file_path, f.ocr_text
        FROM files fp
        JOIN files f ON fp.file_id = f.id
        WHERE fp.person_id = ?
    """, (person_id,))
    files = c.fetchall()

    for file_path, ocr_text in files:
        # Extract events from OCR text using LLaMA data if available
        c.execute("SELECT events FROM ocr_results WHERE file_path=?", (file_path,))
        row = c.fetchone()
        if row and row[0]:
            try:
                events_data = eval(row[0])  # row[0] should be a list of dicts
            except Exception:
                events_data = []
        else:
            events_data = []

        for event in events_data:
            event_type = event.get("type", "Unknown")
            event_date = parse_date(event.get("date", ""))
            description = event.get("description", "")
            c.execute("""
                INSERT INTO person_events (person_id, event_type, event_date, description, source_file)
                VALUES (?, ?, ?, ?, ?)
            """, (person_id, event_type, event_date, description, file_path))

conn.commit()
conn.close()
log.info("Timeline reconstruction completed.")
