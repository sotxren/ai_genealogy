#!/usr/bin/env python3
"""
sync_to_omv.py

Incremental sync of local genealogy project to OMV backup.
- Copies code, models, output, graphs, and web_ui updates
- Skips files that already exist with the same hash
- Offline-safe, read-only to OMV (no execution on OMV)
"""

import os
import shutil
from pathlib import Path
import hashlib
import logging

# -------------------------------
# CONFIG
# -------------------------------
LOCAL_BASE = Path.home() / "genealogy"
OMV_BASE = Path("/mnt/omv/genealogy")

# Folders to sync
FOLDERS = {
    "backup_code": ["*.py"],
    "backup_models": ["models"],
    "backup_output": ["output", "graphs", "web_ui"]
}

LOG_FILE = LOCAL_BASE / ".sync_to_omv.log"

# -------------------------------
# SETUP LOGGING
# -------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("sync_to_omv")
log.info("Starting sync to OMV")

# -------------------------------
# UTILS
# -------------------------------
def file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def sync_file(src: Path, dst: Path):
    """Copy file if missing or changed."""
    ensure_dir(dst.parent)
    if dst.exists():
        if file_hash(src) == file_hash(dst):
            return False  # already synced
    shutil.copy2(src, dst)
    return True

def sync_folder(src: Path, dst: Path, patterns=None):
    """Sync files/folders recursively."""
    copied_count = 0
    if patterns:
        for pattern in patterns:
            for path in src.glob(pattern):
                if path.is_file():
                    dst_path = dst / path.relative_to(src)
                    if sync_file(path, dst_path):
                        copied_count += 1
                elif path.is_dir():
                    dst_path = dst / path.relative_to(src)
                    copied_count += sync_folder(path, dst_path)
    else:
        # copy everything
        for item in src.iterdir():
            dst_path = dst / item.name
            if item.is_dir():
                copied_count += sync_folder(item, dst_path)
            else:
                if sync_file(item, dst_path):
                    copied_count += 1
    return copied_count

# -------------------------------
# MAIN SYNC
# -------------------------------
total_copied = 0
for backup_name, patterns in FOLDERS.items():
    src_path = LOCAL_BASE
    dst_path = OMV_BASE / backup_name
    ensure_dir(dst_path)
    copied = sync_folder(src_path, dst_path, patterns)
    log.info(f"Synced {copied} files/folders to {dst_path}")
    total_copied += copied

log.info(f"Sync complete, total files copied: {total_copied}")
print(f"Sync complete, total files copied: {total_copied}")
