from flask import Flask, render_template
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import time

## reading csv result
import pandas as pd

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/result')
def result():
    file_path='./static/working_file/mockup.csv'
    df=pd.read_csv(file_path)
    result=csv_to_list_of_dicts(file_path)
    print(result)
    return render_template('landing.html',result=result)


@app.route("/analyze", methods=["POST"])
def start_process():
    # Start the long-running process here
    # This may involve running a separate function or spawning a new thread
    
    # For demonstration purposes, let's sleep for 10 seconds
    time.sleep(5)

    # Notify the frontend that the process is complete
    socketio.emit("process_complete", {"message": "Processing task finished"})
    
    return jsonify({"status": "Process completed"})

@app.route("/progress")
def get_progress():
    # Return the progress status to the client
    # You can calculate the progress based on your specific logic
    
    # For demonstration purposes, let's return a random progress value between 0 and 100
    import random
    progress = random.randint(0, 100)
    
    return jsonify({"progress": progress})


import csv

def csv_to_list_of_dicts(file_path):
    data = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    return data


if __name__ == '__main__':
    app.run(debug=True)