#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB = Path.home() / "genealogy/db/family_tree.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id, notes FROM people")
for pid, notes in c.fetchall():
    if not notes:
        continue
    if "born" in notes.lower():
        c.execute("""
        INSERT INTO events (person_id, event_type, title, notes)
        VALUES (?, 'birth', 'Birth inferred', ?)
        """, (pid, notes))

conn.commit()
conn.close()
print("Event timeline built.")
