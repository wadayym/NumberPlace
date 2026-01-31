#!/bin/sh
python -m pip install -r requirements.txt
gunicorn application:app --bind=0.0.0.0:8000 --timeout 600 || sleep infinity