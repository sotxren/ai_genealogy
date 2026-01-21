Foundation code - check comments for updates, "revision 2.x expansion" released 1/20/2026 (26 files currently in updated release)

goal is to have a central point (via folder on external network storage device) where you could dump photo and document scans, in any format, text files, pdfs, whatever, and have the folder scanned for changes, if changes found, have those files copied over to the local host for processing. Processing would include file type determaination (extention), file contents (images, text, mixture), extract data, parse it in a readable and searchable format into a database, append any information to the correct individuals, create an output of timelines, family trees, connections, relationships, ages, birthdates, dates of death, marriages, divorces, etc. Whatever it's fed, gets sorted and applied. I thought I would try to pipe in some a.i. to see if that would help, so I used ollama with an instance of llama3.2 as this is all running on CPU and not a GPU rig. So I am trying to keep this lightweight and resource friendly. 
The setup that this is running on is as follows : desktop pc with an i3:8100 seriez and 32Gb ram, onboard video(not used, no external graphics cards), running linux - Ubuntu server 24.4 - ollama - llama3.2 - a venv created on the host pc, python 3.x , torch (cpu only) , numpy,  and several other prereqs I can't remember at the moment. I have a separate proxmox server that I am running OMV on, that I am using as a central storage depot, as well as intake port. The program will check local folder for changes, then, if available on the network, check network storage. I do appoligize, I just moments ago was able to get the pipeline to work all the way though and give a result. Not a "useable" result, but it's a start. 
Reason for this "idea" : Grandmother passed away a couple years ago, at the time of this writing, I remember growing up, she would type away for hours, every day. Decades. She put together so much information and history on huge portions of our family. Unfortunatly, I was too young and didn't realize the wealth of information she was sharing at the time. Then, over the years, a good portion of research was damaged and destroyed by a flood, but, there is still a large amount that remains. It's been shuffled around and moved over the years, and I would like to have it, all organized, updated, searchable, able to be visualized, "see" the tree and branches and have a timeline, with branches.....for one, forms are boring, and the formats of the chart layout vary, depending if she had already did it in her style on her forms, or if it was still in a different format. There is a person that wrote a book about their branch of the family, I wanted that included and attached to that individual, things like that, build a clickable, visually interesting, searchable, database...with as little user input as possible. I just want to feed the scanner, or dump files in the folder....let the computer do computer things. Hopefully, something useful comes out the other end. I have mountians of documents, decades of work was put into it, so , there's a lot. I'll never get through that stack in my lifetime if I have to do it in a traditional way. Shout out to D.A. on YT, incorporating a.i. into genealogy research. Found when I was searching around to see if I was 'reinventing the wheel'. Usually when there is a program out in the wild, that does what I want, it has commas in the pricetag. I can't find exactly what I want, so...here we are.

And this MUST WORK OFFLINE !!!! cause nothing upsets me more, than trying to run a program, and it has to constantly fetch something from the internet, or it just doesn't work. once you download the models one time, that's it. Use it locally, offline, no internet required. Portability is nice, as is privacy and security.

🧬 Genealogy AI Pipeline (CPU-Only)

A self-healing, modular genealogy processing pipeline that ingests documents and photos, performs OCR, extracts structured data using a local LLM, clusters faces, and generates human-readable HTML outputs — with OpenMediaVault (OMV) used strictly as network storage.

1. System Requirements
Operating System

Ubuntu Server 22.04+ (you can substutute. I just happened to use it)

No GUI required

systemd enabled

Hardware

CPU-only (no GPU, no CUDA)  <--(you can install the gpu files if you have a supporting GPU, I did not)

Minimum:

4 CPU cores recommended

8 GB RAM minimum (16 GB recommended for OCR + LLM)  <---(16 is fine for ollama paired with a smaller llm such as llama3.2:latest, the bottleneck will be CPU)

Storage:

Local disk for processing

Network storage via CIFS (OMV)

2. Network Storage (OMV)
Purpose

OMV is storage only — never execution, never source of truth. (I have write issues to the network share, I can "copy" files, but can not 'write to' files, reason i copy back and forth in this setup.)

Mount

CIFS / SMB share

Auto-mounted at boot via systemd

/mnt/omv/genealogy
├── incoming/        # Intake only (copied to local)
├── processed/       # Copy of completed files
├── html/            # HTML outputs
├── graphs/          # Generated relationship graphs
├── backup_code/     # Backup of *.py pipeline code

Mount Behavior

systemd automount

CIFS v3.0

uid=1000,gid=1000

Read/write

Network latency tolerated

Local disk is authoritative

3. Python Environment
Python

Python 3.10+

Virtual Environment
python3 -m venv venv
source venv/bin/activate

4. Python Dependencies (CPU-Only)
Core
requests
Pillow
easyocr
numpy
opencv-python
sqlite3 (stdlib)

OCR

EasyOCR

CPU-only

Uses PyTorch CPU backend

Custom OCR router:

ocr_engine.py

Can choose engine per file type

Face Processing
face-recognition
dlib (CPU)
scikit-learn

HTML / Graphs
jinja2
networkx

Install
pip install -r requirements.txt

5. Local LLM (CPU-Only)
Ollama

Installed system-wide

No GPU

No HuggingFace runtime dependency

Model
llama3.2

API Endpoint
http://127.0.0.1:11434

Usage

JSON-only extraction

Timeout-protected

Fail-safe (pipeline continues if LLM fails)

6. Database
SQLite

File: ~/genealogy/db/family_tree.db

Schema (Current)
people (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT,
  last_name TEXT,
  birth_date TEXT,
  death_date TEXT
)

files (
  id INTEGER PRIMARY KEY,
  filename TEXT UNIQUE,
  processed_at TEXT,
  ocr_text TEXT
)

ocr_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_hash TEXT UNIQUE,
  file_path TEXT,
  engine TEXT,
  confidence REAL,
  text TEXT
)

face_embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_path TEXT,
  embedding BLOB
)

Upgrades

Handled by db_upgrade.py

Idempotent

Safe to run every cycle

7. Pipeline Layout
Local Directory (Source of Truth)
~/genealogy
├── incoming/        # Files copied here from OMV
├── processed/       # Renamed, timestamped originals
├── html/            # OCR + extraction results
├── graphs/          # Relationship graphs
├── db/
│   └── family_tree.db
├── ocr_ingest.py
├── face_cluster.py
├── db_upgrade.py
├── build_timelines.py
├── generate_graph.py
├── link_assets.py
├── run_all.py       # Pipeline controller
├── ocr_engine.py
└── requirements.txt

8. Pipeline Execution Order

Controlled by run_all.py

1. ocr_ingest.py
   - Sync OMV → local
   - OCR documents/photos
   - Store OCR + hashes
   - LLM structured extraction
   - Generate HTML
   - Move files to processed

2. face_cluster.py
   - Scan images
   - Extract face embeddings
   - Cluster faces
   - Safe skip if no faces

3. db_upgrade.py
   - Schema reconciliation
   - Auto-heal missing tables/columns

4. build_timelines.py
   - Person-centric event timelines

5. generate_graph.py
   - Family relationship graph (HTML)

6. link_assets.py
   - Connect outputs

9. Self-Healing Behavior

The pipeline is fault-tolerant by design:

Missing tables → auto-created

No faces → skip without failure

OCR already done → skipped via hash

OMV unavailable → local continues

LLM failure → OCR still saved

The pipeline never blocks indefinitely.

10. Logging
Log File
~/.genealogy.log

Includes

Per-script start/stop

Errors with stack traces

Skipped conditions

OMV sync activity

11. Backup Strategy
Code Backup
rsync -av ~/genealogy/*.py /mnt/omv/genealogy/backup_code/

Database Backup (Recommended)
cp ~/genealogy/db/family_tree.db /mnt/omv/genealogy/db_backup/

12. Design Principles

Local disk = authority

OMV = storage only

CPU-only

No cloud dependencies

Idempotent

Observable

Recoverable

Status

✔ Working
✔ Stable
✔ CPU-only
✔ Network-tolerant
✔ Ready for incremental improvement
