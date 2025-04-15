"""
WSGI Entry Point for Vercel

This module applies compatibility patches before importing Flask,
then imports and initializes the Flask application.
"""

# Apply compatibility patches first
import werkzeug_patch

# Then import the Flask app
from app import app, db, initialize_database

# Initialize the database
with app.app_context():
    initialize_database()

# Make the app available to Vercel
application = app

# For Vercel serverless deployment
app.debug = False 