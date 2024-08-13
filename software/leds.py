import serial
import time
import serial.tools.list_ports as list_ports

# Hardware brighntess
class HardwareBrightness:
    def __init__(self, port):
        self.port = port
        self.current = None

    def set(self, val):       
        self.current = val
        val = val + 100 # For arduino code

        self.port.write(str(val).encode())
        time.sleep(1.25)
        
    def close(self):
        if self.port.is_open:
            self.port.close()

if __name__ == '__main__':
    leds = HardwareBrightness(serial.Serial('/dev/ttyACM1', 115200))
    leds.set(120)
    v = leds.current
    leds.set(0)
    leds.set(v)

