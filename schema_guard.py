# schema_guard.py
import sqlite3
import logging

log = logging.getLogger("schema_guard")

# ------------------------------------------------------------
# Ensure table exists
# ------------------------------------------------------------
def ensure_table(conn: sqlite3.Connection, ddl: str):
    try:
        conn.execute(ddl)
        conn.commit()
    except Exception as e:
        log.error(f"Failed ensuring table: {e}")

# ------------------------------------------------------------
# Ensure column exists
# ------------------------------------------------------------
def ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    col_type: str = "TEXT",
    default=None
):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in c.fetchall()}

    if column not in cols:
        log.info(f"Adding column {table}.{column}")
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        if default is not None:
            c.execute(
                f"UPDATE {table} SET {column}=? WHERE {column} IS NULL",
                (default,)
            )
        conn.commit()

# ------------------------------------------------------------
# Normalize people.name from first/last
# ------------------------------------------------------------
def normalize_people_name(conn: sqlite3.Connection):
    ensure_column(conn, "people", "name")

    conn.execute("""
        UPDATE people
        SET name = TRIM(
            COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
        )
        WHERE name IS NULL OR name = ''
    """)
    conn.commit()
