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
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['SESSION_COOKIE_NAME'] = 'roast_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 31  # 31 days

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

    # Register routes
    from app.main import register_routes
    register_routes(app)

    return app
