from pymodbus.client.sync import ModbusTcpClient
import time

class TiltSensor:
    def __init__(self, ip, port=8899, slave_id=1):
        self.client = ModbusTcpClient(ip, port=port)
        if not self.client.connect():
            raise ConnectionError(f"Cannot connect to {ip}:{port}")
        self.slave_id = slave_id
        print(" TiltSensor connected")

    @staticmethod
    def _to_signed(v):
        return v - 65536 if v > 32767 else v

    def read_angles(self):
        try:
            rr = self.client.read_holding_registers(0, 3, unit=self.slave_id)
            if (rr is None) or rr.isError():
                print("Modbus error or no response:", rr)
                return None
            rx, ry, rz = rr.registers
            x = self._to_signed(rx) / 100.0
            y = self._to_signed(ry) / 100.0
            z = self._to_signed(rz) / 100.0
            return {"roll": x, "pitch": y, "yaw": z}
        except Exception as e:
            print(" Read error:", e)
            return None

    def close(self):
        self.client.close()

if __name__ == "__main__":
        sensor = TiltSensor("10.10.100.250", port=8899, slave_id=1)
        print("Tilt sensor connected. Reading angles...\n")
        try:
            while True:
                data = sensor.read_angles()
                if data:
                    print(
                        f"Roll: {data['roll']:7.2f}°  "
                        f"Pitch: {data['pitch']:7.2f}°  "
                        f"Yaw: {data['yaw']:7.2f}°"
                    )
                else:
                    print(" No data")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n Stopped by user")
        finally:
            sensor.close()
