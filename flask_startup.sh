#!/bin/bash

cd /home/psu/Desktop/flask
python app.py &
sleep 5
chromium-browser --kiosk http://0.0.0.0:5000 &