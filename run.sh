#!/bin/bash

# This script starts the Gunicorn server for the Service Topology Agent.

echo "Starting Gunicorn server..."

# We point Gunicorn to the Flask app object inside our app.py file.
# The configuration is loaded from gunicorn_config.py.
gunicorn --config gunicorn_config.py app:app 