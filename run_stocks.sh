#!/bin/bash

# Kill any existing instances
pkill -f "python app.py" || true

# Log file
LOG_FILE="stock_dashboard.log"

# Function to start the app
start_app() {
  echo "Starting stock dashboard application at $(date)" >> $LOG_FILE
  python app.py >> $LOG_FILE 2>&1
  echo "Application stopped at $(date). Restarting..." >> $LOG_FILE
}

# Keep restarting the app if it crashes
while true; do
  start_app
  sleep 2
done 