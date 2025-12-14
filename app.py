from flask import Flask, request, jsonify, render_template
import serial, glob, threading

BAUD = 9600
app = Flask(__name__)

# Auto-detect USB ports
ports = sorted(glob.glob("/dev/ttyUSB*"))

motors = {}
logs = []

for i, p in enumerate(ports):
    try:
        motors[f"m{i+1}"] = serial.Serial(p, BAUD, timeout=0.2)
    except:
        pass

def read_serial():
    while True:
        for k, s in motors.items():
            try:
                if s.in_waiting:
                    msg = s.readline().decode().strip()
                    logs.append(f"{k}: {msg}")
                    logs[:] = logs[-50:]
            except:
                pass

threading.Thread(target=read_serial, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html", motors=list(motors.keys()))

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    cmd = int(data["cmd"], 16)

    for m in data["targets"]:
        motors[m].write(bytes([cmd]))

    return jsonify(ok=True)

@app.route("/logs")
def get_logs():
    return jsonify(logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

