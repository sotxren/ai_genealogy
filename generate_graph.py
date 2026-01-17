#!/usr/bin/env python3

import sqlite3
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import shutil
import os
from datetime import datetime

BASE = Path.home() / "genealogy"
DB = BASE / "db" / "family_tree.db"
GRAPH_DIR = BASE / "graphs"
GRAPH_DIR.mkdir(exist_ok=True)

OMV = Path("/mnt/omv/genealogy")
OMV_AVAILABLE = OMV.exists() and os.access(OMV, os.W_OK)
OMV_GRAPH = OMV / "graphs" if OMV_AVAILABLE else None

def build_graph():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    G = nx.Graph()

    for row in c.execute("SELECT id, name FROM people"):
        G.add_node(row[0], label=row[1])

    for row in c.execute("SELECT person1, relation, person2 FROM relationships"):
        G.add_edge(row[0], row[2], label=row[1])

    conn.close()
    return G

def export_graph(G):
    net = Network(height="800px", width="100%", bgcolor="#111", font_color="white")
    net.from_nx(G)

    out = GRAPH_DIR / "family_graph.html"
    net.write_html(out.as_posix())

    if OMV_AVAILABLE:
        shutil.copy2(out, OMV_GRAPH / f"family_graph_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html")

if __name__ == "__main__":
    G = build_graph()
    export_graph(G)
