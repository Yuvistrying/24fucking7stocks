#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "python app.py" || true

# Start with supervisor
echo "Starting stock app with supervisor..."
supervisord -c stocks_supervisor.conf

# Show status
echo "Supervisor status:"
supervisorctl -c stocks_supervisor.conf status

echo ""
echo "=================================================="
echo "The stock app is now running reliably in the background."
echo "To check status: supervisorctl -c stocks_supervisor.conf status"
echo "To stop: supervisorctl -c stocks_supervisor.conf stop stocks"
echo "To start: supervisorctl -c stocks_supervisor.conf start stocks"
echo "To restart: supervisorctl -c stocks_supervisor.conf restart stocks"
echo "To view logs: tail -f stocks_supervisor.log"
echo "==================================================" 