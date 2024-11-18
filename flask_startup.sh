#!/bin/bash

cd /home/psu/Desktop/flask
python3 app.py &
sleep 5
chromium-browser --start-fullscreen http://localhost:5000