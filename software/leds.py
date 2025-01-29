import time
import json

with open('./app_config.json', 'r') as conf:
    app_conf = json.load(conf)
    lec_version = app_conf['LEC_version']

if lec_version == 'V2':
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

elif lec_version == 'V3':
    import board
    import adafruit_ds3502

    def rescale(value, min1, max1, min2, max2):
        return ((value - min1) / (max1 - min1)) * (max2 - min2) + min2

    # Hardware brighntess
    class HardwareBrightness:
        def __init__(self, addr=None):
            i2c = board.I2C() 
            self.device = adafruit_ds3502.DS3502(i2c)
            self.current = None

        def set(self, val):       
            self.current = round(rescale(val, 0, 100, 0, 127)) # rescale to 0-127, ds3502 wiper range
            self.device.wiper = self.current
            time.sleep(1.25)
            
        def close(self):
            return

else:
    raise ValueError('LEC version not recognised, only V2 and V3 currently supported.')

if __name__ == '__main__':
    leds = HardwareBrightness()
    leds.set(25)
    leds.set(0)

