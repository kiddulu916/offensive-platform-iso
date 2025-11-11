#!/bin/bash

# Navigate to app directory
cd /platform-app

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export QT_QPA_PLATFORM=xcb
export DISPLAY=:0

# Launch application in fullscreen
python3 main.py --fullscreen

# If app crashes, restart it
while true; do
    echo "Application crashed. Restarting in 5 seconds..."
    sleep 5
    python3 main.py --fullscreen
done