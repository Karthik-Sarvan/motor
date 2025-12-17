from pymodbus.client import ModbusSerialClient

class TiltSensor:
    def __init__(self, port="/dev/ttyUSB1", baud=4800, timeout=1):
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baud,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=timeout
        )

        if not self.client.connect():
            raise ConnectionError("❌ Cannot connect to Tilt Sensor")

        print("✅ TiltSensor connected")

    @staticmethod
    def _to_signed(v):
        return v - 65536 if v > 32767 else v

    def read_angles(self):
        try:
            rx = self.client.read_holding_registers(0).registers[0]
            ry = self.client.read_holding_registers(1).registers[0]
            rz = self.client.read_holding_registers(2).registers[0]

            x = self._to_signed(rx) / 100.0
            y = self._to_signed(ry) / 100.0
            z = self._to_signed(rz) / 100.0

            return x, y, z

        except Exception as e:
            print("❌ Exception:", e)
            return None, None, None

    def close(self):
        self.client.close()
