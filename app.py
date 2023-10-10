from flask import Flask, render_template
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('landing.html')


@app.route("/start", methods=["POST"])
def start_process():
    # Start the long-running process here
    # This may involve running a separate function or spawning a new thread
    
    # For demonstration purposes, let's sleep for 10 seconds
    time.sleep(10)

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


if __name__ == '__main__':
    app.run(debug=True)