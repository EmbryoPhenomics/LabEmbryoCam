import serial
import time
import serial.tools.list_ports as list_ports

# Hardware brighntess
class HardwareBrightness:
    def __init__(self, port):
        self.port = serial.Serial(port, 115200)
        self.current = None

    def set(self, val):
        self.current = val
        val = val + 100 # For arduino code

        if self.port:
            self.port.write(str(val).encode())
            time.sleep(0.05)

    def close(self):
        if self.port:
            self.port.close()

if __name__ == '__main__':
    leds = HardwareBrightness('/dev/ttyACM2')
    time.sleep(1)
    leds.set(120)
    time.sleep(1)
    v = leds.current
    leds.set(0)
    time.sleep(1)
    leds.set(v)

