#!/usr/bin/env python3
"""
Face clustering for genealogy images.

- Reads images from incoming/processed folders
- Extracts face embeddings
- Groups similar faces with DBSCAN
- Stores in face_embeddings table
- Does not overwrite existing embeddings
"""

import sqlite3
from pathlib import Path
import face_recognition
import numpy as np
from sklearn.cluster import DBSCAN
import base64
import traceback
import logging

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path.home() / "genealogy"
DB_PATH = BASE_DIR / "db/family_tree.db"
PHOTO_DIRS = [
    BASE_DIR / "incoming",
    BASE_DIR / "processed"
]

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------------
# Connect DB
# -----------------------------
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

logging.info("Starting face clustering...")

# -----------------------------
# ENSURE TABLE EXISTS (FIX)
# -----------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS face_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    file_path TEXT UNIQUE,
    face_encoding TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

logging.info("Starting face clustering...")

# -----------------------------
# Load already-processed face files
# -----------------------------
c.execute("SELECT file_path FROM face_embeddings")
already_done = {row[0] for row in c.fetchall()}

# -----------------------------
# Gather images
# -----------------------------
image_files = []
for d in PHOTO_DIRS:
    if not d.exists():
        continue
    for f in d.glob("*"):
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"] and str(f) not in already_done:
            image_files.append(f)

if not image_files:
    logging.info("No new images to process.")
    conn.close()
    exit(0)

encodings = []
paths = []

# -----------------------------
# Extract face embeddings
# -----------------------------
for img_path in image_files:
    try:
        img = face_recognition.load_image_file(str(img_path))
        faces = face_recognition.face_encodings(img)
        if not faces:
            continue

        for face_encoding in faces:
            encodings.append(face_encoding)
            paths.append(str(img_path))

    except Exception as e:
        logging.warning(f"Failed processing {img_path}: {e}")
        traceback.print_exc()

if not encodings:
    logging.info("No faces found.")
    conn.close()
    exit(0)

X = np.array(encodings)

# -----------------------------
# Cluster faces
# -----------------------------
clustering = DBSCAN(
    eps=0.55,
    min_samples=2,
    metric="euclidean"
).fit(X)

labels = clustering.labels_
logging.info(f"Found {len(set(labels)) - (1 if -1 in labels else 0)} clusters")

# -----------------------------
# Store results
# -----------------------------
for label, encoding, path in zip(labels, encodings, paths):
    if label == -1:
        continue  # noise / unknown

    encoded = base64.b64encode(encoding.tobytes()).decode("utf-8")

    try:
        c.execute("""
            INSERT INTO face_embeddings (person_id, file_path, face_encoding)
            VALUES (?, ?, ?)
        """, (None, path, encoded))
    except Exception as e:
        logging.error(f"Failed to insert {path}: {e}")
        traceback.print_exc()

conn.commit()
conn.close()
logging.info("Face clustering completed.")
