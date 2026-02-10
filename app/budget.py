"""Monthly budget tracking — monthly_budget table is the single source of truth for spend."""

import logging
from datetime import datetime, timezone

from app.db import get_db
from app.config import get_config

logger = logging.getLogger(__name__)


def get_current_month() -> str:
    """Return current month as 'YYYY-MM'."""
    return datetime.now(timezone.utc).strftime('%Y-%m')


def get_month_spend(month: str = None) -> float:
    """Get total spend for a month. Defaults to current month."""
    month = month or get_current_month()
    with get_db() as db:
        row = db.execute(
            "SELECT spent_cents FROM monthly_budget WHERE month = ?", (month,)
        ).fetchone()
        return row['spent_cents'] if row else 0.0


def get_month_roast_count(month: str = None) -> int:
    """Get roast count for a month. Defaults to current month."""
    month = month or get_current_month()
    with get_db() as db:
        row = db.execute(
            "SELECT roast_count FROM monthly_budget WHERE month = ?", (month,)
        ).fetchone()
        return row['roast_count'] if row else 0


def record_cost(cost_cents: float) -> None:
    """Atomic upsert — no drift possible."""
    month = get_current_month()
    with get_db() as db:
        db.execute("""
            INSERT INTO monthly_budget (month, spent_cents, roast_count, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (month) DO UPDATE SET
                spent_cents = spent_cents + ?,
                roast_count = roast_count + 1,
                updated_at = CURRENT_TIMESTAMP
        """, (month, cost_cents, cost_cents))


def check_budget() -> tuple[bool, str]:
    """Can we afford another roast?"""
    budget_limit = float(get_config('monthly_budget_cents', '2000'))
    current_spend = get_month_spend()

    if current_spend >= budget_limit:
        return False, "The roast machine is cooling down. Check back next month."

    estimated_next = float(get_config('cost_per_roast_cents', '1'))
    if current_spend + estimated_next > budget_limit:
        return False, "The roast machine is cooling down. Check back next month."

    # Warning threshold check (for logging, not user-facing)
    threshold = float(get_config('budget_warning_threshold', '80'))
    if budget_limit > 0 and (current_spend / budget_limit * 100) >= threshold:
        logger.warning(
            "Budget warning: %.1f%% used (%.2f / %.2f cents)",
            current_spend / budget_limit * 100, current_spend, budget_limit
        )

    return True, "ok"


def get_monthly_history() -> list[dict]:
    """Get all monthly budget records for admin panel."""
    with get_db() as db:
        rows = db.execute(
            "SELECT month, spent_cents, roast_count, updated_at "
            "FROM monthly_budget ORDER BY month DESC"
        ).fetchall()
        return [dict(row) for row in rows]
