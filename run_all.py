#!/usr/bin/env python3
"""
Pipeline controller with watchdog.
THIS is the only daemon loop.
"""

import subprocess
import time
import logging
from pathlib import Path
import sys

BASE = Path.home() / "genealogy"
PYTHON = str(BASE / "venv" / "bin" / "python")
LOG_FILE = BASE / "run_all.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("run_all")
log.info("Pipeline controller started")

PIPELINE = [
    "ocr_ingest.py",
    "face_cluster.py",
    "db_upgrade.py",
    "build_timelines.py",
    "generate_graph.py",
    "link_assets.py"
]

WATCHDOG_TIMEOUT = 600  # seconds

def run_step(script):
    cmd = [PYTHON, str(BASE / script)]
    log.info(f"Running: {script}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    start = time.time()
    while True:
        if proc.poll() is not None:
            break
        if time.time() - start > WATCHDOG_TIMEOUT:
            proc.kill()
            log.error(f"Watchdog killed {script}")
            return False
        time.sleep(2)

    out, err = proc.communicate()
    if out:
        log.info(out.strip())
    if err:
        log.error(err.strip())

    if proc.returncode != 0:
        log.error(f"{script} failed")
        return False

    log.info(f"{script} completed")
    return True

# ============================================================
# MAIN LOOP
# ============================================================
try:
    while True:
        for step in PIPELINE:
            if not run_step(step):
                log.warning("Pipeline aborted this cycle")
                break

        log.info("Pipeline cycle complete — sleeping")
        time.sleep(120)

except KeyboardInterrupt:
    log.info("Pipeline stopped by user")
    sys.exit(0)
