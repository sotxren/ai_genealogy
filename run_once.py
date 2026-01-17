#!/usr/bin/env python3
import subprocess
from pathlib import Path
import logging
import sys

# ============================================================
BASE = Path.home() / "genealogy"
LOG_FILE = BASE / "run_once.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
log = logging.getLogger("genealogy")
log.info("Single-pass pipeline started")

PYTHON = str(BASE / "venv" / "bin" / "python")

PIPELINE_STEPS = [
    [PYTHON, str(BASE / "ocr_ingest.py")],
    [PYTHON, str(BASE / "face_cluster.py")],
    [PYTHON, str(BASE / "db_upgrade.py")],
    [PYTHON, str(BASE / "build_timelines.py")],
    [PYTHON, str(BASE / "generate_graph.py")],
    [PYTHON, str(BASE / "link_assets.py")],
]

def run_step(cmd):
    log.info(f"Starting: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate()
        if stdout:
            log.info(stdout.strip())
        if stderr:
            log.error(stderr.strip())
        if proc.returncode != 0:
            log.error(f"Step failed with code {proc.returncode}: {' '.join(cmd)}")
            return False
    except Exception as e:
        log.error(f"Exception running step {' '.join(cmd)}: {e}")
        return False
    log.info(f"Step completed successfully: {' '.join(cmd)}")
    return True

def main():
    for step in PIPELINE_STEPS:
        success = run_step(step)
        if not success:
            log.warning(f"Aborting pipeline due to failure: {' '.join(step)}")
            sys.exit(1)
    log.info("Single-pass pipeline complete")

if __name__ == "__main__":
    main()
