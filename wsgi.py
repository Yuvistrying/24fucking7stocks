from app import app, db, initialize_database

# Initialize the database on startup
with app.app_context():
    initialize_database()

# For Vercel serverless deployment
from app import app as application 