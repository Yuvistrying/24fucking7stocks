try:
    from app import app, db, initialize_database

    # Initialize the database on startup
    with app.app_context():
        try:
            initialize_database()
            print("Database initialization complete")
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            # Continue anyway - we might be able to connect later

    # For Vercel serverless deployment
    app.debug = False

    # This is the WSGI application object that Vercel will use
    application = app
except Exception as e:
    import traceback
    print(f"Error in wsgi.py: {str(e)}")
    traceback.print_exc()
    raise 