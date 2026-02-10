"""App configuration table interface (get/set)."""

from app.db import get_db


def get_config(key: str, default: str = None) -> str | None:
    """Get a config value by key."""
    with get_db() as db:
        row = db.execute(
            "SELECT value FROM app_config WHERE key = ?", (key,)
        ).fetchone()
        return row['value'] if row else default


def set_config(key: str, value: str) -> None:
    """Set a config value. Updates updated_at timestamp."""
    with get_db() as db:
        db.execute(
            """UPDATE app_config
               SET value = ?, updated_at = CURRENT_TIMESTAMP
               WHERE key = ?""",
            (value, key)
        )


def get_all_config() -> list[dict]:
    """Get all config entries for the admin panel."""
    with get_db() as db:
        rows = db.execute(
            "SELECT key, value, description, updated_at FROM app_config ORDER BY key"
        ).fetchall()
        return [dict(row) for row in rows]
