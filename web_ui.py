#!/usr/bin/env python3

from flask import Flask, render_template_string
import sqlite3
from pathlib import Path

BASE = Path.home() / "genealogy"
DB = BASE / "db" / "family_tree.db"

app = Flask(__name__)

HTML = """
<h1>Genealogy System</h1>

<h2>People</h2>
<ul>
{% for p in people %}
<li>{{p[1]}}</li>
{% endfor %}
</ul>

<h2>Documents</h2>
<ul>
{% for f in files %}
<li>{{f[1]}}</li>
{% endfor %}
</ul>

<h2>Graphs</h2>
<a href="/graphs/family_graph.html">Family Graph</a>
"""

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    people = list(c.execute("SELECT * FROM people"))
    files = list(c.execute("SELECT * FROM files"))
    conn.close()
    return render_template_string(HTML, people=people, files=files)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
