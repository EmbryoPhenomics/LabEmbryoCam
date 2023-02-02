from serial.tools import list_ports
import serial
import time

def check_devices():
    ports = list_ports.grep('/dev/ttyACM*')
    names = [p.device for p in ports]

    light_port = None
    joystick_port = None
    xyz_port = None

    for p in names:
        port = serial.Serial(p, 115200)
        time.sleep(1)

        out = str(port.readline())

        if 'light' in out:
            print('Light: ' + p)
            light_port = p
        elif 'joystick' in out:
            print('Manual controls: ' + p)
            joystick_port = p
        else:
            print('Stage: ' + p)
            xyz_port = p

        port.close()

    return light_port, joystick_port, xyz_port

check_devices()