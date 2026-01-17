#!/usr/bin/env python3

import sqlite3

DB = "/home/USER/genealogy/db/family_tree.db"

def setup():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS search_index
    USING fts5(content)
    """)

    c.execute("DELETE FROM search_index")

    for row in c.execute("SELECT first_name,last_name,notes FROM people"):
        c.execute("INSERT INTO search_index VALUES (?)",
                  (" ".join(filter(None,row)),))

    for row in c.execute("SELECT ocr_text FROM files"):
        if row[0]:
            c.execute("INSERT INTO search_index VALUES (?)", (row[0],))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup()
