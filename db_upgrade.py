#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import logging

BASE_DIR = Path.home() / "genealogy"
DB_PATH = BASE_DIR / "db/family_tree.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cursor.fetchall()]

def table_exists(cursor, table):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

logging.info("Starting database upgrade check...")

# PEOPLE
if not table_exists(c, "people"):
    c.execute("""
        CREATE TABLE people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            birth_date TEXT,
            death_date TEXT,
            notes TEXT
        )
    """)
    logging.info("Created table: people")

# FILES
if not table_exists(c, "files"):
    c.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            file_type TEXT,
            file_name TEXT,
            file_path TEXT,
            ocr_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    """)
    logging.info("Created table: files")

# OCR RESULTS (HASH-BASED, NO REPROCESS LOOPS)
if not table_exists(c, "ocr_results"):
    c.execute("""
        CREATE TABLE ocr_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT UNIQUE,
            file_path TEXT,
            engine TEXT,
            confidence REAL,
            text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logging.info("Created table: ocr_results")

# RELATIONSHIPS
if not table_exists(c, "relationships"):
    c.execute("""
        CREATE TABLE relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            related_person_id INTEGER,
            relationship_type TEXT,
            FOREIGN KEY(person_id) REFERENCES people(id),
            FOREIGN KEY(related_person_id) REFERENCES people(id)
        )
    """)
    logging.info("Created table: relationships")

# FACE EMBEDDINGS
if not table_exists(c, "face_embeddings"):
    c.execute("""
        CREATE TABLE face_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            file_path TEXT,
            face_encoding TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    """)
    logging.info("Created table: face_embeddings")

# EVENTS
if not table_exists(c, "events"):
    c.execute("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            event_type TEXT,
            event_date TEXT,
            description TEXT,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    """)
    logging.info("Created table: events")

# LOCATIONS
if not table_exists(c, "locations"):
    c.execute("""
        CREATE TABLE locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            latitude REAL,
            longitude REAL,
            notes TEXT
        )
    """)
    logging.info("Created table: locations")

# SOURCES
if not table_exists(c, "sources"):
    c.execute("""
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            source_type TEXT,
            citation TEXT,
            url TEXT,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    """)
    logging.info("Created table: sources")

conn.commit()
conn.close()
logging.info("Database upgrade complete.")
