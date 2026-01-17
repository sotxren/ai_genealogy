#!/usr/bin/env python3

import sqlite3
from pathlib import Path
import re

BASE = Path.home() / "genealogy"
DB = BASE / "db" / "family_tree.db"

def normalize(s):
    return re.sub(r"[^a-z]", "", s.lower())

def link():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS asset_links (
        file_id INTEGER,
        person_id INTEGER,
        confidence REAL
    )
    """)

    files = list(c.execute("SELECT id, filename, ocr_text FROM files"))
    people = list(c.execute("SELECT id, name FROM people"))

    for fid, fname, text in files:
        text_n = normalize(fname + " " + (text or ""))

        for pid, name in people:
            if normalize(name) in text_n:
                c.execute(
                    "INSERT INTO asset_links VALUES (?, ?, ?)",
                    (fid, pid, 0.85)
                )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    link()
