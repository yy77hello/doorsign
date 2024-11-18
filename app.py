import os
from flask import Flask, render_template, request, jsonify
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from flask import send_file
from contextlib import contextmanager
import serial
import platform
import logging
import subprocess
import socket
from flask import Flask

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Global serial object
ser = None

@contextmanager
def get_serial_connection():
    global ser
    if ser is None or not ser.is_open:
        try:
            if platform.system() == "Windows":
                ser = serial.Serial('COM3', 115200, timeout=1)
            else:
                ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)  # Default for Raspberry Pi
            logging.info("Serial port opened successfully")
        except serial.SerialException as e:
            logging.error(f"Error opening serial port: {e}")
            ser = None
    
    try:
        yield ser
    finally:
        if ser is not None and ser.is_open:
            ser.close()
            logging.info("Serial port closed")

# Default values
room_name = "Room"
room_status = "Closed"
messages = []
office_hours = "Not set"
current_message = ""

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def index():
    global room_name, room_status, office_hours
    current_time = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
    return render_template('index.html', room_name=room_name, room_status=room_status,
                           office_hours=office_hours, current_time=current_time)

@app.route('/navigate', methods=['GET', 'POST'])
def navigate():
    if request.method == 'POST':
        destination = request.form['destination']
        # Call the external Python script
        subprocess.run(['python', 'process_navigation.py', destination])
        # Redirect to the route display page
        return redirect(url_for('display_route'))
    return render_template('navigate.html')

@app.route('/display_route')
def display_route():
    return send_file('route.jpg', mimetype='image/jpeg')

@app.route('/take_picture')
def take_picture():
    with get_serial_connection() as serial_conn:
        if serial_conn is not None and serial_conn.is_open:
            logging.info("Sending command to take picture")
            send_command_to_esp32('take_picture', serial_conn)
            return '', 204  # No content response

def send_command_to_esp32(command, serial_conn):
    if serial_conn is not None and serial_conn.is_open:
        try:
            serial_conn.write(command.encode())
            logging.debug(f"Command sent: {command}")
        except serial.SerialException as e:
            logging.error(f"Error sending command: {e}")
            raise

@app.route('/mgmt', methods=['GET', 'POST'])
def mgmt():
    global room_name, room_status, office_hours, current_message, messages

    if request.method == 'POST':
        if 'room_name' in request.form:
            room_name = request.form['room_name']
        elif 'message' in request.form:
            current_message = request.form['message']
        elif 'office_hours' in request.form:
            office_hours = request.form['office_hours']

    return render_template('mgmt.html', room_name=room_name, room_status=room_status,
                           office_hours=office_hours, current_message=current_message, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages.append({"text": message, "timestamp": timestamp})
    return jsonify({"status": "success"})

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)

@app.route('/clear_messages', methods=['POST'])
def clear_messages():
    global messages
    messages.clear()
    return jsonify({"status": "success"})

@app.route('/updates')
def updates():
    global room_name, room_status, current_message, office_hours
    current_time = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
    return jsonify({
        'current_time': current_time,
        'room_status': room_status,
        'current_message': current_message,
        'office_hours': office_hours,
        'room_name': room_name
    })

@app.route('/update_status', methods=['POST'])
def update_status():
    global room_status
    statuses = ["Closed", "Open", "Busy"]
    current_index = statuses.index(room_status)
    room_status = statuses[(current_index + 1) % len(statuses)]
    return jsonify({'status': 'success', 'new_status': room_status})

if __name__ == '__main__':
    ip_address = get_ip_address()
    print(f" * Running on http://{ip_address}:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)