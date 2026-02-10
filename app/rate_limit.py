"""Layered rate limiting: session -> IP ceiling -> global cap."""

import hashlib
import os
from datetime import date, datetime, timedelta

from flask import session, request

from app.db import get_db
from app.config import get_config


def get_ip_hash() -> str:
    """Hash the IP. Never store raw IPs.

    Uses X-Forwarded-For only when TRUSTED_PROXY_COUNT is set (i.e. behind
    a known reverse proxy). Otherwise falls back to remote_addr to prevent
    IP spoofing via forged headers.
    """
    trusted_proxies = int(os.environ.get('TRUSTED_PROXY_COUNT', '0'))
    if trusted_proxies > 0 and request.access_route:
        # access_route is the X-Forwarded-For chain; pick the client IP
        # by counting back from the rightmost (closest to our proxy)
        idx = max(0, len(request.access_route) - trusted_proxies)
        ip = request.access_route[idx]
    else:
        ip = request.remote_addr or '127.0.0.1'
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def check_rate_limit() -> tuple[bool, str]:
    """Returns (allowed, reason). Checks session first, then IP ceiling, then global."""
    today = date.today().isoformat()
    session_id = session.get('session_id', get_ip_hash())
    ip_hash = get_ip_hash()

    with get_db() as db:
        # Check 1: Session-based limit (primary)
        row = db.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM daily_usage WHERE date = ? AND identity = ?",
            (today, f"session:{session_id}")
        ).fetchone()
        session_count = row['total']

        session_limit = int(get_config('daily_roasts_per_session', '10'))
        if session_count >= session_limit:
            remaining_hours = 24 - datetime.now().hour
            return False, f"Easy there, glutton for punishment. You've used all {session_limit} roasts for today. Resets in ~{remaining_hours}h."

        # Check 2: IP ceiling (anti-abuse backstop)
        row = db.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM daily_usage WHERE date = ? AND identity = ?",
            (today, f"ip:{ip_hash}")
        ).fetchone()
        ip_count = row['total']

        ip_ceiling = int(get_config('daily_roasts_per_ip', '30'))
        if ip_count >= ip_ceiling:
            return False, "This network has hit its daily limit. Try again tomorrow."

        # Check 3: Global daily cap
        row = db.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM daily_usage WHERE date = ?",
            (today,)
        ).fetchone()
        global_count = row['total']

        global_cap = int(get_config('daily_roasts_global', '500'))
        if global_count >= global_cap:
            return False, "The roast machine is at capacity for today. Check back tomorrow."

    return True, "ok"


def record_usage() -> None:
    """Call after a successful roast. Increments both session and IP counters."""
    today = date.today().isoformat()
    session_id = session.get('session_id', get_ip_hash())
    ip_hash = get_ip_hash()

    with get_db() as db:
        for identity in [f"session:{session_id}", f"ip:{ip_hash}"]:
            db.execute("""
                INSERT INTO daily_usage (date, identity, count) VALUES (?, ?, 1)
                ON CONFLICT (date, identity) DO UPDATE SET count = count + 1
            """, (today, identity))


def get_remaining_roasts() -> int:
    """Get remaining roasts for the current session."""
    today = date.today().isoformat()
    session_id = session.get('session_id', get_ip_hash())

    with get_db() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM daily_usage WHERE date = ? AND identity = ?",
            (today, f"session:{session_id}")
        ).fetchone()
        used = row['total']

    limit = int(get_config('daily_roasts_per_session', '10'))
    return max(0, limit - used)


def prune_old_usage(days_to_keep: int = 7) -> None:
    """Delete usage records older than N days."""
    cutoff = (date.today() - timedelta(days=days_to_keep)).isoformat()
    with get_db() as db:
        db.execute("DELETE FROM daily_usage WHERE date < ?", (cutoff,))
