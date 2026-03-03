import os
import psycopg2
import psycopg2.extras
from flask import current_app, g

def get_db():
    """Get database connection per request"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(
                host=os.environ.get('DB_HOST'),
                port=os.environ.get('DB_PORT', '5432'),
                database=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                sslmode=os.environ.get('DB_SSLMODE', 'require'),
                connect_timeout=30
            )
        except Exception as e:
            current_app.logger.error(f"Database connection failed: {e}")
            raise
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db)
