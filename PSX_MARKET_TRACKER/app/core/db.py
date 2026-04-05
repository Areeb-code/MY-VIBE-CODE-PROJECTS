"""
PSX Platform — Database Layer
SQLite database with users, portfolio, and alerts tables.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime


def _get_db_path() -> str:
    """Returns the path to the SQLite database file."""
    # Allow override for testing
    env_path = os.environ.get("DB_PATH")
    if env_path:
        return os.path.abspath(env_path)

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "psx_platform.db")


def get_connection():
    """Returns a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database schema. Safe to call multiple times."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'broker', 'client')),
            broker_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (broker_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broker_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('BUY', 'SELL')),
            date TEXT NOT NULL,
            note TEXT DEFAULT '',
            FOREIGN KEY (broker_id) REFERENCES users(id),
            FOREIGN KEY (client_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broker_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            limit_upper REAL DEFAULT 0.0,
            limit_lower REAL DEFAULT 0.0,
            UNIQUE(client_id, symbol),
            FOREIGN KEY (broker_id) REFERENCES users(id),
            FOREIGN KEY (client_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_portfolio_broker ON portfolio(broker_id);
        CREATE INDEX IF NOT EXISTS idx_portfolio_client ON portfolio(client_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_client ON alerts(client_id);
        CREATE INDEX IF NOT EXISTS idx_users_broker ON users(broker_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)
    
    conn.commit()
    conn.close()


def has_owner():
    """Check if an owner account exists in the database."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'owner'").fetchone()
    conn.close()
    return row['cnt'] > 0


def migrate_from_json():
    """
    Migrate existing JSON portfolio data into the database for a specific user.
    Called during first-run migration if old JSON data exists.
    Returns True if migration was performed, False otherwise.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    portfolio_json = os.path.join(base_dir, "data", "portfolio.json")
    
    if not os.path.exists(portfolio_json):
        return False
    
    try:
        with open(portfolio_json, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False
    
    transactions = data.get("transactions", [])
    alerts_data = data.get("alerts", {})
    
    if not transactions and not alerts_data:
        return False
    
    return {
        "transactions": transactions,
        "alerts": alerts_data
    }


def import_json_for_user(user_id, broker_id, json_data):
    """
    Import JSON portfolio data into the database for a specific user.
    json_data should be the dict returned by migrate_from_json().
    """
    if not json_data:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    transactions = json_data.get("transactions", [])
    alerts_data = json_data.get("alerts", {})
    
    for t in transactions:
        cursor.execute("""
            INSERT INTO portfolio (broker_id, client_id, symbol, quantity, price, type, date, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            broker_id, user_id,
            str(t.get('symbol', '')),
            int(t.get('quantity', 0)),
            float(t.get('price', 0.0)),
            str(t.get('type', 'BUY')).upper(),
            str(t.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            str(t.get('note', ''))
        ))
    
    for symbol, alert in alerts_data.items():
        cursor.execute("""
            INSERT OR REPLACE INTO alerts (broker_id, client_id, symbol, limit_upper, limit_lower)
            VALUES (?, ?, ?, ?, ?)
        """, (
            broker_id, user_id,
            str(symbol),
            float(alert.get('limit_upper', 0.0)),
            float(alert.get('limit_lower', 0.0))
        ))
    
    conn.commit()
    conn.close()


# ─── Tenant Filter ─────────────────────────────────────────────────────────────

def tenant_where(session, table_prefix=""):
    """
    Returns a (where_clause, params) tuple for tenant-based filtering.
    This MUST be used on every sensitive data query.
    
    Args:
        session: Session object with role, user_id, broker_id
        table_prefix: Optional table alias prefix (e.g. "p." for portfolio)
    
    Returns:
        (where_sql, params_tuple)
    """
    p = table_prefix
    
    if session.role == 'owner':
        return ("1=1", ())
    elif session.role == 'broker':
        return (f"{p}broker_id = ?", (session.user_id,))
    elif session.role == 'client':
        return (f"{p}client_id = ?", (session.user_id,))
    else:
        # Unknown role — deny everything
        return ("1=0", ())
