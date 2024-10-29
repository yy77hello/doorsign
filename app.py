from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Default values
room_name = "Room"
room_status = "Closed"
messages = []
office_hours = "Not set"

@app.route('/')
def index():
    global room_name, room_status, office_hours
    current_time = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
    return render_template('index.html', room_name=room_name, room_status=room_status,
                           office_hours=office_hours, current_time=current_time)

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
    app.run(debug=True, host='0.0.0.0', port=5000)
