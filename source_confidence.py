#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB = Path.home() / "genealogy/db/family_tree.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id, source_type FROM sources")
for sid, stype in c.fetchall():
    conf = {
        "letter": 0.9,
        "photo": 0.7,
        "newspaper": 0.8,
        "llm": 0.5
    }.get(stype, 0.4)

    c.execute("UPDATE sources SET confidence=? WHERE id=?", (conf, sid))

conn.commit()
conn.close()
print("Confidence scoring complete.")
