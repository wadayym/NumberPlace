#!/bin/sh
apt update && sudo apt install libxcb1
python -m pip install -r requirements.txt
gunicorn --bind=0.0.0.0 --timeout 600 application:app