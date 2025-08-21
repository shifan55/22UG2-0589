import os
import time
from datetime import datetime
from flask import Flask, request, redirect, render_template_string, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv("DB_HOST", "mydb")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "secret")

app = Flask(__name__)

BASE_HTML = r"""
<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Notes — Flask + Postgres</title>
  <style>
    :root {
      --bg: #0b1320;
      --card: #111a2b;
      --text: #e6edf3;
      --muted: #9fb2c8;
      --accent: #7c9aff;
      --accent-2: #4ce1b6;
      --danger: #ff6b6b;
      --border: #21304a;
      --input: #0f192a;
      --shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    [data-theme="light"] {
      --bg: #f6f8fb;
      --card: #ffffff;
      --text: #0e1726;
      --muted: #5b6b81;
      --accent: #365df3;
      --accent-2: #1ea97c;
      --danger: #d64545;
      --border: #e5e9f2;
      --input: #f1f4f9;
      --shadow: 0 10px 30px rgba(6,24,44,0.1);
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }
    a { color: var(--accent); text-decoration: none; }
    .container { max-width: 960px; margin: 0 auto; padding: 24px; }
    .topbar {
      display: flex; gap: 16px; align-items: center; justify-content: space-between;
      margin-bottom: 20px;
    }
    .brand { display: flex; gap: 12px; align-items: center; }
    .brand-logo {
      width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, var(--accent), var(--accent-2)); box-shadow: var(--shadow);
    }
    .brand h1 { font-size: 22px; margin: 0; font-weight: 700; letter-spacing: 0.2px; }
    .muted { color: var(--muted); }
    .card {
      background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px 18px; box-shadow: var(--shadow);
    }
    .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    @media (min-width: 900px) { .grid-2 { grid-template-columns: 1.2fr 1fr; } }
    .input, textarea {
      width: 100%; border: 1px solid var(--border); background: var(--input);
      color: var(--text); border-radius: 12px; padding: 12px 14px; font-size: 15px; outline: none;
    }
    textarea { min-height: 120px; resize: vertical; }
    .btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      border: 1px solid transparent; background: var(--accent); color: #fff;
      padding: 10px 16px; border-radius: 12px; font-weight: 600; cursor: pointer; transition: transform .05s ease;
      box-shadow: 0 6px 16px rgba(54,93,243,.25);
    }
    .btn:active { transform: translateY(1px); }
    .btn.secondary { background: transparent; color: var(--text); border-color: var(--border); }
    .btn.success { background: var(--accent-2); box-shadow: 0 6px 16px rgba(30,169,124,.25); }
    .btn.danger { background: var(--danger); box-shadow: 0 6px 16px rgba(214,69,69,.25); }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .spacer { height: 10px; }
    .note {
      border: 1px dashed var(--border); border-radius: 14px; padding: 12px; background: transparent;
    }
    .note-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .note-time { font-size: 12px; color: var(--muted); }
    .note-actions { display: flex; gap: 8px; }
    .list { display: grid; gap: 12px; }
    .pill {
      display:inline-flex; align-items:center; gap:8px; font-size:12px; border:1px solid var(--border);
      padding:6px 10px; border-radius:999px; background: var(--card);
    }
    .searchbar { display: flex; gap: 10px; align-items: center; }
    .hidden { display: none; }
    .footer { text-align:center; font-size: 12px; margin-top: 24px; color: var(--muted);}
    .toggle {
      border: 1px solid var(--border); padding: 8px 12px; border-radius: 12px; background: var(--card); cursor: pointer;
    }
    .inline-edit {
      width: 100%; border: 1px solid var(--border); background: var(--input); color: var(--text);
      border-radius: 10px; padding: 8px 10px; font-size: 14px; outline: none;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="topbar">
      <div class="brand">
        <div class="brand-logo" aria-hidden="true"></div>
        <div>
          <h1>Notes</h1>
          <div class="muted">Flask (8000) ↔ PostgreSQL (5432) with persistent volume</div>
        </div>
      </div>
      <div class="row">
        <span class="pill">Status: <span id="db-status">checking…</span></span>
        <button id="themeToggle" class="toggle" title="Toggle theme">🌙/☀️</button>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h2 style="margin: 0 0 8px;">Add a note</h2>
        <p class="muted" style="margin-top:0">Your notes are saved in Postgres. Try stopping and starting containers—your data remains.</p>
        <form class="row" method="POST" action="/add">
          <textarea name="content" placeholder="Type something helpful…" required></textarea>
          <div class="row">
            <button class="btn" type="submit">Save note</button>
            <button class="btn secondary" type="reset">Clear</button>
          </div>
        </form>
      </div>

      <div class="card">
        <h2 style="margin: 0 0 8px;">Search</h2>
        <div class="searchbar">
          <form class="row" method="GET" action="/">
            <input class="input" type="text" name="q" placeholder="Filter notes…" value="{{ search or '' }}" />
            <button class="btn secondary" type="submit">Search</button>
            {% if search %}
              <a class="btn secondary" href="/">Reset</a>
            {% endif %}
          </form>
        </div>
        <div class="spacer"></div>
        <div class="muted">Found <strong>{{ notes|length }}</strong> note{{ '' if notes|length == 1 else 's' }}.</div>
      </div>
    </div>

    <div class="spacer"></div>

    <div class="card">
      <h2 style="margin: 0 0 8px;">All Notes</h2>
      <div class="list">
        {% for n in notes %}
          <div class="note" data-note-id="{{ n.id }}">
            <div class="note-header">
              <div class="note-time">#{{ n.id }} • {{ n.created_at_fmt }}</div>
              <div class="note-actions">
                <button class="btn secondary" onclick="startEdit({{ n.id | int }})">Edit</button>
                <form method="POST" action="/delete/{{ n.id }}" onsubmit="return confirm('Delete this note?');">
                  <button class="btn danger" type="submit">Delete</button>
                </form>
              </div>
            </div>
            <div class="spacer"></div>
            <div class="note-content" id="content-view-{{ n.id }}">{{ n.content }}</div>
            <form id="content-edit-{{ n.id }}" class="hidden" method="POST" action="/edit/{{ n.id }}">
              <div class="row" style="gap:8px; align-items: stretch;">
                <textarea class="inline-edit" name="content">{{ n.content }}</textarea>
                <button class="btn success" type="submit">Save</button>
                <button class="btn secondary" type="button" onclick="cancelEdit({{ n.id }})">Cancel</button>
              </div>
            </form>
          </div>
        {% else %}
          <p class="muted">No notes yet. Add your first one!</p>
        {% endfor %}
      </div>
    </div>

    <div class="footer">Dockerized demo • Persistent Postgres volume • Theme preference saved locally</div>
  </div>

  <script>
    // Theme toggle with localStorage
    const root = document.documentElement;
    const current = localStorage.getItem('theme') || 'light';
    root.setAttribute('data-theme', current);
    document.getElementById('themeToggle').addEventListener('click', () => {
      const t = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', t);
      localStorage.setItem('theme', t);
    });

    // Inline edit helpers
    function startEdit(id) {
      document.getElementById(`content-view-${id}`).classList.add('hidden');
      document.getElementById(`content-edit-${id}`).classList.remove('hidden');
    }
    function cancelEdit(id) {
      document.getElementById(`content-view-${id}`).classList.remove('hidden');
      document.getElementById(`content-edit-${id}`).classList.add('hidden');
    }

    // Quick DB status check
    fetch('/health').then(r => r.json()).then(d => {
      const el = document.getElementById('db-status');
      el.textContent = d.ok ? 'connected' : 'unavailable';
      if (!d.ok) el.style.color = '#ff6b6b';
    }).catch(() => {
      const el = document.getElementById('db-status');
      el.textContent = 'unavailable';
      el.style.color = '#ff6b6b';
    });
  </script>
</body>
</html>
"""

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        connect_timeout=5
    )

def ensure_table(retries=40, delay=1.5):
    """
    Ensure the notes table exists and has a created_at column.
    Waits for DB to be ready since the containers may start in parallel.
    """
    last_err = None
    for _ in range(retries):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL
                    )
                """)
                # Add created_at if not exists
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='notes' AND column_name='created_at'
                        ) THEN
                            ALTER TABLE notes
                            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                        END IF;
                    END $$;
                """)
                conn.commit()
                return
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError(f"Database not ready after retries: {last_err}")

def fetch_notes(search=None):
    q = """
        SELECT id, content, created_at
        FROM notes
    """
    args = []
    if search:
        q += " WHERE content ILIKE %s"
        args.append(f"%{search}%")
    q += " ORDER BY id DESC"
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(q, args)
        rows = cur.fetchall()
    # Format created_at nicely
    for r in rows:
        if r.get("created_at"):
            dt = r["created_at"]
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except Exception:
                    dt = None
            r["created_at_fmt"] = dt.strftime("%Y-%m-%d %H:%M") if dt else "-"
        else:
            r["created_at_fmt"] = "-"
    return rows

@app.route("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(ok=True)
    except Exception:
        return jsonify(ok=False), 503

@app.get("/")
def index():
    search = request.args.get("q", "").strip() or None
    notes = fetch_notes(search=search)
    return render_template_string(BASE_HTML, notes=notes, search=search)

@app.post("/add")
def add():
    content = (request.form.get("content") or "").strip()
    if content:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO notes(content) VALUES (%s)", (content,))
            conn.commit()
    return redirect("/")

@app.post("/delete/<int:note_id>")
def delete(note_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM notes WHERE id=%s", (note_id,))
        conn.commit()
    return redirect("/")

@app.post("/edit/<int:note_id>")
def edit(note_id: int):
    content = (request.form.get("content") or "").strip()
    if content:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE notes SET content=%s WHERE id=%s", (content, note_id))
            conn.commit()
    return redirect("/")

if __name__ == "__main__":
    ensure_table()
    app.run(host="0.0.0.0", port=8000)
