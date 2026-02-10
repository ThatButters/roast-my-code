"""Database initialization, connection management, and schema creation."""

import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.environ.get('DATABASE_URL', 'sqlite:///data/roasts.db').replace('sqlite:///', '')

SCHEMA = """
-- App configuration (admin-editable)
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monthly budget tracking (SOURCE OF TRUTH for spend)
CREATE TABLE IF NOT EXISTS monthly_budget (
    month TEXT PRIMARY KEY,
    spent_cents REAL DEFAULT 0,
    roast_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roast history and cost tracking
CREATE TABLE IF NOT EXISTS roast_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    ip_hash TEXT,
    input_chars INTEGER,
    input_lines INTEGER,
    input_tokens_actual INTEGER,
    output_tokens_actual INTEGER,
    cost_cents REAL,
    model TEXT,
    mode TEXT DEFAULT 'roast',
    severity TEXT DEFAULT 'normal',
    language_detected TEXT,
    share_id TEXT UNIQUE,
    is_public INTEGER DEFAULT 0,
    roast_score INTEGER,
    roast_content TEXT,
    code_content TEXT
);

-- Daily rate limit tracking (session + IP counters)
CREATE TABLE IF NOT EXISTS daily_usage (
    date TEXT,
    identity TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (date, identity)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_roast_log_share_id ON roast_log(share_id);
CREATE INDEX IF NOT EXISTS idx_roast_log_created ON roast_log(created_at);
CREATE INDEX IF NOT EXISTS idx_daily_usage_date ON daily_usage(date);
"""

DEFAULT_CONFIG = [
    ('monthly_budget_cents', '2000', 'Max monthly spend in cents ($20.00)'),
    ('cost_per_roast_cents', '1', 'Estimated cost per roast (Haiku default)'),
    ('max_input_chars', '15000', 'Max characters per submission (~3K tokens)'),
    ('max_input_lines', '500', 'Max lines per submission'),
    ('daily_roasts_per_session', '10', 'Free roasts per session per day'),
    ('daily_roasts_per_ip', '30', 'Hard ceiling per IP per day (anti-abuse)'),
    ('daily_roasts_global', '500', 'Global daily roast cap'),
    ('enable_roasting', 'true', 'Kill switch - disable all roasting'),
    ('default_model', 'claude-haiku-4-5-20251001', 'Default model'),
    ('budget_warning_threshold', '80', 'Alert at this % of monthly budget'),
]


def get_db_path():
    """Resolve the database file path, ensuring the directory exists."""
    db_path = DATABASE_PATH
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


def get_connection():
    """Get a new database connection with WAL mode and busy timeout."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema and seed default config."""
    with get_db() as db:
        db.executescript(SCHEMA)
        for key, value, description in DEFAULT_CONFIG:
            db.execute(
                """INSERT INTO app_config (key, value, description)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO NOTHING""",
                (key, value, description)
            )
        db.commit()
