from flask import Flask, request, jsonify, render_template
import serial, glob, threading, time

BAUD = 115200
app = Flask(__name__)

# Auto-detect USB ports
ports = sorted(glob.glob("/dev/ttyUSB*"))

motors = {}
logs = []

for i, p in enumerate(ports):
    try:
        motors[f"m{i+1}"] = serial.Serial(p, BAUD, timeout=0.1)
        time.sleep(2)  # allow Arduino reset
    except:
        pass

def read_serial():
    while True:
        for k, s in motors.items():
            try:
                while s.in_waiting:
                    b = s.read(1)
                    code = b[0]

                    meaning = {
                        0x55: "ACK",
                        0xAB: "ERR",
                        0xE1: "MAX LIMIT",
                        0xE0: "MIN LIMIT",
                        0xEE: "SYS_RDY"
                    }.get(code, f"0x{code:02X}")

                    logs.append(f"{k}: {meaning}")
                    logs[:] = logs[-50:]
            except:
                pass
        time.sleep(0.01)

threading.Thread(target=read_serial, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html", motors=list(motors.keys()))

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    cmd = int(data["cmd"], 16)

    for m in data["targets"]:
        if m in motors:
            motors[m].write(bytes([cmd]))

    return jsonify(ok=True)

@app.route("/logs")
def get_logs():
    return jsonify(logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
