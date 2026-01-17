#!/usr/bin/env python3
import sqlite3
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
DB_PATH = Path.home() / "genealogy" / "db" / "family_tree.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Connect/create DB
# -----------------------------
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# -----------------------------
# People
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    death_date TEXT,
    notes TEXT,
    source_doc TEXT
)
''')

# -----------------------------
# Relationships
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    related_person_id INTEGER,
    relationship_type TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(related_person_id) REFERENCES people(id)
)
''')

# -----------------------------
# Files (photos, letters, documents)
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    file_type TEXT,       -- "photo", "letter", "article", etc.
    file_name TEXT,
    file_path TEXT,
    ocr_text TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id)
)
''')

# -----------------------------
# Locations (home, work, school, etc.)
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT             -- "home", "work", "school", etc.
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS person_locations (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    location_id INTEGER,
    notes TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
)
''')

# -----------------------------
# Sources, Mentions, Publications
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    source_type TEXT,     -- "book", "newspaper", "letter", etc.
    title TEXT,
    content TEXT,
    file_path TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id)
)
''')

# -----------------------------
# Events (education, work, life events, marriages, moves, etc.)
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    event_type TEXT,      -- "marriage", "graduation", "job", etc.
    title TEXT,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    notes TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id)
)
''')

# -----------------------------
# Faces
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    image_path TEXT,
    face_encoding BLOB,
    FOREIGN KEY(person_id) REFERENCES people(id)
)
''')

conn.commit()
conn.close()
print("Database created/updated with full genealogy schema.")
