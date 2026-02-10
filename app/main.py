"""Routes: landing, result, admin, health."""

import os
import secrets
import logging
from functools import wraps

from flask import (
    render_template, request, redirect, url_for, session,
    flash, jsonify, abort, Response
)

from app.db import get_db
from app.config import get_config, set_config, get_all_config
from app.budget import check_budget, record_cost, get_month_spend, get_month_roast_count, get_monthly_history
from app.rate_limit import check_rate_limit, record_usage, get_remaining_roasts, get_ip_hash
from app.roaster import roast_code
from app.security import validate_input, render_roast_markdown, generate_share_id, get_roast_preview

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes on the Flask app."""

    @app.before_request
    def ensure_session():
        """Ensure every visitor has a session ID for rate limiting."""
        if 'session_id' not in session:
            session['session_id'] = secrets.token_urlsafe(16)
            session.permanent = True

    # --- Public Routes ---

    @app.route('/')
    def index():
        remaining = get_remaining_roasts()
        # Get recent public roasts for the feed
        with get_db() as db:
            recent_roasts = db.execute(
                """SELECT share_id, roast_score, language_detected, mode, created_at,
                          substr(roast_content, 1, 200) as preview
                   FROM roast_log
                   WHERE is_public = 1 AND share_id IS NOT NULL
                   ORDER BY created_at DESC LIMIT 10"""
            ).fetchall()
            recent_roasts = [dict(r) for r in recent_roasts]

        return render_template('index.html',
                               remaining_roasts=remaining,
                               recent_roasts=recent_roasts)

    @app.route('/roast', methods=['POST'])
    def submit_roast():
        code = request.form.get('code', '')
        mode = request.form.get('mode', 'roast')
        severity = request.form.get('severity', 'normal')
        is_public = request.form.get('is_public') == 'on'

        # Validate mode and severity
        if mode not in ('roast', 'waldorf', 'serious'):
            mode = 'roast'
        if severity not in ('gentle', 'normal', 'brutal', 'unhinged'):
            severity = 'normal'

        # Check kill switch
        if get_config('enable_roasting', 'true') != 'true':
            flash("The roast machine is currently offline. Check back later.", "error")
            return redirect(url_for('index'))

        # Validate input
        valid, error_msg = validate_input(code)
        if not valid:
            flash(error_msg, "error")
            return redirect(url_for('index'))

        # Check budget
        budget_ok, budget_msg = check_budget()
        if not budget_ok:
            flash(budget_msg, "error")
            return redirect(url_for('index'))

        # Check rate limit
        rate_ok, rate_msg = check_rate_limit()
        if not rate_ok:
            flash(rate_msg, "error")
            return redirect(url_for('index'))

        # Perform the roast
        try:
            result = roast_code(code, mode=mode, severity=severity)
        except Exception as e:
            logger.error("Roast failed: %s", e)
            flash("Claude is having a moment. Your code was SO bad it broke the reviewer. (Just kidding — try again in a minute.)", "error")
            return redirect(url_for('index'))

        # Generate share ID and store result
        share_id = generate_share_id()
        score = result.get('score')

        with get_db() as db:
            db.execute("""
                INSERT INTO roast_log
                    (session_id, ip_hash, input_chars, input_lines,
                     input_tokens_actual, output_tokens_actual, cost_cents,
                     model, mode, severity, language_detected, share_id,
                     is_public, roast_score, roast_content, code_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.get('session_id'),
                get_ip_hash(),
                len(code),
                len(code.split('\n')),
                result['input_tokens'],
                result['output_tokens'],
                result['cost_cents'],
                result['model'],
                mode,
                severity,
                result['language'],
                share_id,
                1 if is_public else 0,
                score,
                result['roast'],
                code if is_public else None,
            ))

        # Record cost and usage (only for successful roasts)
        if result['cost_cents'] > 0:
            record_cost(result['cost_cents'])
        record_usage()

        return redirect(url_for('view_roast', share_id=share_id))

    @app.route('/roast/<share_id>')
    def view_roast(share_id):
        with get_db() as db:
            roast = db.execute(
                "SELECT * FROM roast_log WHERE share_id = ?", (share_id,)
            ).fetchone()

        if not roast:
            abort(404)

        roast = dict(roast)
        roast_html = render_roast_markdown(roast['roast_content'])
        preview = get_roast_preview(roast['roast_content'])

        return render_template('result.html',
                               roast=roast,
                               roast_content=roast_html,
                               score=roast['roast_score'],
                               share_id=share_id,
                               mode=roast['mode'],
                               preview=preview,
                               remaining_roasts=get_remaining_roasts())

    @app.route('/health')
    def health():
        """For Docker healthcheck and uptime monitoring."""
        try:
            with get_db() as db:
                db.execute("SELECT 1")
            budget_ok = check_budget()[0]
            return jsonify({"status": "ok", "roasting_enabled": budget_ok}), 200
        except Exception as e:
            return jsonify({"status": "error", "detail": str(e)}), 500

    # --- Admin Routes ---

    def require_admin(f):
        """Basic auth decorator for admin routes."""
        @wraps(f)
        def decorated(*args, **kwargs):
            admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme')
            auth = request.authorization
            if not auth or auth.password != admin_password:
                return Response(
                    'Admin access required.',
                    401,
                    {'WWW-Authenticate': 'Basic realm="Admin"'}
                )
            return f(*args, **kwargs)
        return decorated

    @app.route('/admin')
    @require_admin
    def admin():
        config = get_all_config()
        budget_limit = float(get_config('monthly_budget_cents', '2000'))
        current_spend = get_month_spend()
        roast_count = get_month_roast_count()
        monthly_history = get_monthly_history()

        budget_pct = (current_spend / budget_limit * 100) if budget_limit > 0 else 0

        from datetime import datetime, timezone
        import calendar
        now = datetime.now(timezone.utc)
        day_of_month = now.day
        if day_of_month > 0 and current_spend > 0:
            daily_rate = current_spend / day_of_month
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            projected = daily_rate * days_in_month
        else:
            projected = 0

        with get_db() as db:
            recent_logs = db.execute(
                """SELECT id, created_at, input_chars, input_tokens_actual,
                          output_tokens_actual, cost_cents, model, mode,
                          severity, language_detected, roast_score, share_id
                   FROM roast_log ORDER BY created_at DESC LIMIT 50"""
            ).fetchall()
            recent_logs = [dict(r) for r in recent_logs]

        return render_template('admin.html',
                               config=config,
                               current_spend=current_spend,
                               budget_limit=budget_limit,
                               budget_pct=budget_pct,
                               roast_count=roast_count,
                               projected=projected,
                               monthly_history=monthly_history,
                               recent_logs=recent_logs)

    @app.route('/admin/config', methods=['POST'])
    @require_admin
    def update_config():
        for key in request.form:
            if key.startswith('config_'):
                config_key = key[7:]
                set_config(config_key, request.form[key])
        flash("Configuration updated.", "success")
        return redirect(url_for('admin'))

    # --- Error Handlers ---

    @app.errorhandler(404)
    def not_found(e):
        return render_template('base.html', error="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error="Something went wrong."), 500


# For gunicorn: `app.main:app`
from app import create_app
app = create_app()
