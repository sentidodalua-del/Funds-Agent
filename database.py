import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "data/funds_agent.db"

def get_conn():
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            program TEXT,
            managing_entity TEXT,
            area TEXT,
            deadline TEXT,
            total_budget TEXT,
            max_per_project TEXT,
            support_rate TEXT,
            official_link TEXT,
            source TEXT,
            relevance_score INTEGER,
            relevance_label TEXT,
            eligibility_analysis TEXT,
            eligible_components TEXT,
            proposed_budget TEXT,
            proposal_text TEXT,
            next_steps TEXT,
            urgency TEXT,
            investment_profile TEXT,
            raw_data TEXT,
            found_at TEXT,
            is_read INTEGER DEFAULT 0,
            is_saved INTEGER DEFAULT 0,
            saved_at TEXT,
            saved_notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT,
            status TEXT,
            opportunities_found INTEGER,
            opportunities_new INTEGER,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_opportunity(opp: dict):
    conn = get_conn()
    # Check if already exists by title + program
    existing = conn.execute(
        "SELECT id FROM opportunities WHERE title = ? AND program = ?",
        (opp.get("title"), opp.get("program"))
    ).fetchone()
    if existing:
        conn.close()
        return False  # Already exists
    conn.execute("""
        INSERT INTO opportunities (
            title, program, managing_entity, area, deadline,
            total_budget, max_per_project, support_rate, official_link,
            source, relevance_score, relevance_label, eligibility_analysis,
            eligible_components, proposed_budget, proposal_text,
            next_steps, urgency, investment_profile, raw_data, found_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        opp.get("title"), opp.get("program"), opp.get("managing_entity"),
        opp.get("area"), opp.get("deadline"), opp.get("total_budget"),
        opp.get("max_per_project"), opp.get("support_rate"), opp.get("official_link"),
        opp.get("source"), opp.get("relevance_score"), opp.get("relevance_label"),
        opp.get("eligibility_analysis"), opp.get("eligible_components"),
        opp.get("proposed_budget"), opp.get("proposal_text"),
        opp.get("next_steps"), opp.get("urgency"),
        json.dumps(opp), datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return True

def get_all_opportunities(relevance_filter=None, area_filter=None):
    conn = get_conn()
    query = "SELECT * FROM opportunities WHERE 1=1"
    params = []
    if relevance_filter:
        query += " AND relevance_label = ?"
        params.append(relevance_filter)
    if area_filter:
        query += " AND area LIKE ?"
        params.append(f"%{area_filter}%")
    query += " ORDER BY relevance_score DESC, found_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_opportunity_by_id(opp_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM opportunities").fetchone()["c"]
    high = conn.execute("SELECT COUNT(*) as c FROM opportunities WHERE relevance_label = 'Alta'").fetchone()["c"]
    medium = conn.execute("SELECT COUNT(*) as c FROM opportunities WHERE relevance_label = 'Média'").fetchone()["c"]
    low = conn.execute("SELECT COUNT(*) as c FROM opportunities WHERE relevance_label = 'Baixa'").fetchone()["c"]
    today = conn.execute(
        "SELECT COUNT(*) as c FROM opportunities WHERE found_at LIKE ?",
        (datetime.now().strftime("%Y-%m-%d") + "%",)
    ).fetchone()["c"]
    last_search = conn.execute(
        "SELECT ran_at FROM search_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "total": total,
        "high_relevance": high,
        "medium_relevance": medium,
        "low_relevance": low,
        "found_today": today,
        "last_search": last_search["ran_at"] if last_search else None
    }

def log_search(status: str, found: int, new: int, error: str = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO search_logs (ran_at, status, opportunities_found, opportunities_new, error) VALUES (?,?,?,?,?)",
        (datetime.now().isoformat(), status, found, new, error)
    )
    conn.commit()
    conn.close()

def toggle_save(opp_id: int, notes: str = None) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT is_saved FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Not found"}
    new_state = 0 if row["is_saved"] else 1
    saved_at = datetime.now().isoformat() if new_state else None
    conn.execute(
        "UPDATE opportunities SET is_saved = ?, saved_at = ?, saved_notes = ? WHERE id = ?",
        (new_state, saved_at, notes, opp_id)
    )
    conn.commit()
    conn.close()
    return {"is_saved": bool(new_state), "saved_at": saved_at}

def get_saved_opportunities():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM opportunities WHERE is_saved = 1 ORDER BY saved_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_saved_notes(opp_id: int, notes: str):
    conn = get_conn()
    conn.execute("UPDATE opportunities SET saved_notes = ? WHERE id = ?", (notes, opp_id))
    conn.commit()
    conn.close()
