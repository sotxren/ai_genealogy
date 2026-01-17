#!/usr/bin/env python3
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
import logging

# ============================================================
# PATHS + LOGGING
# ============================================================
BASE = Path.home() / "genealogy"
DB_PATH = BASE / "db/family_tree.db"

logging.basicConfig(
    filename=BASE / ".genealogy_identity.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("identity_resolver")
log.info("Identity resolver initialized")

# ============================================================
# DATABASE
# ============================================================
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ============================================================
# HELPER: NAME SIMILARITY
# ============================================================
def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# ============================================================
# FETCH ALL PEOPLE
# ============================================================
c.execute("SELECT id, name FROM people")
people = c.fetchall()

# ============================================================
# CLEAR OLD SCORES
# ============================================================
c.execute("DELETE FROM identity_scores")
conn.commit()

# ============================================================
# CALCULATE PAIRWISE SIMILARITY
# ============================================================
threshold = 0.75  # configurable similarity threshold

for i in range(len(people)):
    id1, name1 = people[i]
    for j in range(i + 1, len(people)):
        id2, name2 = people[j]

        score = similarity(name1, name2)
        if score >= threshold:
            c.execute(
                """
                INSERT INTO identity_scores (person_a, person_b, score, reason)
                VALUES (?, ?, ?, ?)
                """,
                (id1, id2, score, "Name similarity")
            )

conn.commit()
conn.close()
log.info("Identity resolution completed.")
