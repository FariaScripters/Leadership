#!/bin/bash
set -e

# Give some time for the system to settle
sleep 5

# List files in the current directory to verify content
ls -la

# Start Chrome with remote debugging
google-chrome-stable --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --no-sandbox --disable-dev-shm-usage --headless &

# Wait for Chrome to start
until curl --output /dev/null --silent --head --fail http://localhost:9222; do
    printf '.'
    sleep 1
done

# Start FastAPI application
uvicorn app.entrypoint:app --host 0.0.0.0 --port 8000
