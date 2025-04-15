"""
WSGI Entry Point for Vercel

This module applies compatibility patches before importing Flask,
then imports and initializes the Flask application.
"""

# Apply compatibility patches first
import werkzeug_patch
import os
import sys
import traceback
import time

# Set up proper error handling for Vercel
def log_error(message):
    """Log error messages to stderr for Vercel logging"""
    print(message, file=sys.stderr)
    sys.stderr.flush()

# Check if we're in a serverless environment
IS_VERCEL = os.environ.get('VERCEL') == '1'
IS_DEVELOPMENT = os.environ.get('FLASK_ENV') == 'development'

try:
    # Then import the Flask app
    from app import app, db
    
    # Attempt to perform a database health check
    if IS_VERCEL:
        try:
            # Log database configuration (without credentials)
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'postgres' in db_url or 'postgresql' in db_url:
                # Extract just the hostname for logging
                import re
                host_match = re.search(r'@([^:@/]+)', db_url)
                host = host_match.group(1) if host_match else 'unknown-host'
                print(f"Database connection configured to: {host}")
        except Exception as e:
            log_error(f"Failed to log database info: {str(e)}")
    
    # In serverless environments, we need to avoid initializing 
    # the database on cold starts, as it can cause timeouts
    if not IS_VERCEL or IS_DEVELOPMENT:
        from app import initialize_database
        with app.app_context():
            initialize_database()
    else:
        print("Running in Vercel serverless environment - skipping automatic database initialization")
        # For Vercel, we'll initialize the database lazily on first request
    
    # Make the app available to Vercel
    application = app
    
    # For Vercel serverless deployment
    app.debug = False
    
    # Add a handler for lazy database initialization on Vercel
    if IS_VERCEL:
        @app.before_request
        def before_request():
            if not getattr(app, '_database_initialized', False):
                from app import initialize_database
                try:
                    with app.app_context():
                        initialize_database()
                    app._database_initialized = True
                    print("Database initialized on first request")
                except Exception as e:
                    log_error(f"Error initializing database on first request: {e}")
                    log_error(traceback.format_exc())
        
        # Add a standard health check endpoint
        @app.route('/api/health')
        def health_check():
            """Basic health check endpoint for Vercel"""
            from flask import jsonify
            
            # Check database connection if possible
            db_status = "unknown"
            try:
                with app.app_context():
                    # Simple database query that shouldn't fail
                    db.session.execute("SELECT 1").fetchone()
                    db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
            
            return jsonify({
                "status": "ok",
                "timestamp": time.time(),
                "environment": "vercel" if IS_VERCEL else "development",
                "database": db_status
            })

except Exception as e:
    log_error(f"Error during application initialization: {str(e)}")
    log_error(traceback.format_exc())
    
    # Provide a minimal app for Vercel to avoid deployment failures
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error_index():
        return jsonify({
            "status": "error",
            "message": "Application failed to initialize",
            "error": str(e)
        }), 500
    
    application = app 