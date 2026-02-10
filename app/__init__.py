"""Flask app factory for Roast My Code."""

import os
import secrets
import logging

from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Configuration
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        logging.warning("SECRET_KEY not set — using random key (sessions won't survive restarts)")
        secret_key = secrets.token_hex(32)
    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_NAME'] = 'roast_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 7 days
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB max request body

    # Logging
    logging.basicConfig(level=logging.INFO)

    # CSRF protection
    csrf.init_app(app)

    # Initialize database
    from app.db import init_db
    with app.app_context():
        init_db()

    # Prune old usage on startup
    from app.rate_limit import prune_old_usage
    with app.app_context():
        try:
            prune_old_usage()
        except Exception:
            pass  # non-critical on startup

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://code.iconify.design; "
            "style-src 'self' 'unsafe-inline' https://api.fontshare.com; "
            "font-src https://api.fontshare.com https://cdn.fontshare.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://api.iconify.design; "
            "frame-ancestors 'none'"
        )
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Register routes
    from app.main import register_routes
    register_routes(app)

    return app
