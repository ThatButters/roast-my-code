"""Tests for budget tracking."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up a temp database before importing app modules
_tmpdir = tempfile.mkdtemp()
os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(_tmpdir, "test.db")}'

from app.db import init_db, get_db
from app.budget import get_month_spend, record_cost, check_budget, get_current_month


def setup_function():
    """Reset database before each test."""
    init_db()
    with get_db() as db:
        db.execute("DELETE FROM monthly_budget")


def test_initial_spend_is_zero():
    assert get_month_spend() == 0.0


def test_record_cost():
    record_cost(1.5)
    assert get_month_spend() == 1.5


def test_record_cost_accumulates():
    record_cost(1.0)
    record_cost(2.5)
    record_cost(0.5)
    assert get_month_spend() == 4.0


def test_check_budget_ok():
    ok, msg = check_budget()
    assert ok is True
    assert msg == "ok"


def test_check_budget_exceeded():
    # Set budget to 10 cents
    with get_db() as db:
        db.execute("UPDATE app_config SET value = '10' WHERE key = 'monthly_budget_cents'")

    # Record 10 cents of spending
    record_cost(10.0)

    ok, msg = check_budget()
    assert ok is False
    assert "cooling down" in msg


def test_check_budget_would_exceed():
    # Set budget to 5 cents, cost_per_roast to 2
    with get_db() as db:
        db.execute("UPDATE app_config SET value = '5' WHERE key = 'monthly_budget_cents'")
        db.execute("UPDATE app_config SET value = '2' WHERE key = 'cost_per_roast_cents'")

    record_cost(4.0)

    ok, msg = check_budget()
    assert ok is False


def test_get_current_month_format():
    month = get_current_month()
    assert len(month) == 7  # 'YYYY-MM'
    assert month[4] == '-'
