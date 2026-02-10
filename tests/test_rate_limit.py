"""Tests for rate limiting."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up a temp database before importing app modules
_tmpdir = tempfile.mkdtemp()
os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(_tmpdir, "test.db")}'

from flask import Flask
from app.db import init_db, get_db
from app.rate_limit import check_rate_limit, record_usage, get_remaining_roasts, prune_old_usage


def make_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    return app


def setup_function():
    """Reset database before each test."""
    init_db()
    with get_db() as db:
        db.execute("DELETE FROM daily_usage")


def test_rate_limit_allows_first_request():
    app = make_app()
    with app.test_request_context():
        from flask import session
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['session_id'] = 'test-session-123'
            with client.application.test_request_context():
                session['session_id'] = 'test-session-123'
                ok, msg = check_rate_limit()
                assert ok is True


def test_remaining_roasts_default():
    app = make_app()
    with app.test_request_context():
        from flask import session
        session['session_id'] = 'test-session-456'
        remaining = get_remaining_roasts()
        assert remaining == 10  # default limit


def test_record_usage_decrements_remaining():
    app = make_app()
    with app.test_request_context():
        from flask import session
        session['session_id'] = 'test-session-789'
        record_usage()
        remaining = get_remaining_roasts()
        assert remaining == 9


def test_session_limit_enforced():
    app = make_app()
    with app.test_request_context():
        from flask import session
        session['session_id'] = 'test-session-limit'

        # Set session limit to 3 for testing
        with get_db() as db:
            db.execute("UPDATE app_config SET value = '3' WHERE key = 'daily_roasts_per_session'")

        # Use all 3
        for _ in range(3):
            record_usage()

        ok, msg = check_rate_limit()
        assert ok is False
        assert "roasts" in msg.lower() or "used all" in msg.lower()


def test_prune_old_usage():
    # Insert old data
    with get_db() as db:
        db.execute(
            "INSERT INTO daily_usage (date, identity, count) VALUES ('2020-01-01', 'session:old', 5)"
        )

    prune_old_usage(days_to_keep=1)

    with get_db() as db:
        row = db.execute("SELECT count(*) as c FROM daily_usage WHERE date = '2020-01-01'").fetchone()
        assert row['c'] == 0
