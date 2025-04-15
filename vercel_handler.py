from flask import Flask, request
import json
import os

# Import your app
from app import app as flask_app

def handler(event, context):
    """
    Vercel serverless function handler for Flask
    """
    path = event.get('path', '/')
    http_method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    
    # Convert Vercel's request format to WSGI format
    environ = {
        'wsgi.input': None,  # No input stream for simplicity
        'wsgi.errors': None,  # No error stream for simplicity
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.url_scheme': headers.get('x-forwarded-proto', 'http'),
        'SERVER_SOFTWARE': 'Vercel',
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': event.get('queryStringParameters', {}),
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': headers.get('content-length', ''),
        'REMOTE_ADDR': headers.get('x-forwarded-for', ''),
        'SERVER_NAME': headers.get('host', 'localhost'),
        'SERVER_PORT': headers.get('x-forwarded-port', '80'),
        'SERVER_PROTOCOL': 'HTTP/1.1',
    }
    
    # Add HTTP headers
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Execute the Flask application
    response_data = {
        'statusCode': 200,
        'headers': {},
        'body': '',
    }
    
    def start_response(status, response_headers, exc_info=None):
        status_code = int(status.split(' ')[0])
        response_data['statusCode'] = status_code
        for key, value in response_headers:
            response_data['headers'][key] = value
    
    try:
        # Initialize the database
        from app import initialize_database, db
        with flask_app.app_context():
            initialize_database()
        
        # Execute the Flask application
        body = b''.join(flask_app(environ, start_response))
        response_data['body'] = body.decode('utf-8')
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        response_data['statusCode'] = 500
        response_data['body'] = json.dumps({
            'error': error_msg,
            'traceback': traceback_str
        })
    
    return response_data 