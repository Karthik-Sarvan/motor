import time
from tilt_sensor import TiltSensor

sensor = TiltSensor(port="/dev/ttyUSB1", baud=4800)

while True:
    x, y, z = sensor.read_angles()
    print(f"X={x:+6.2f}°  Y={y:+6.2f}°  Z={z:+6.2f}°")
    time.sleep(0.5)
