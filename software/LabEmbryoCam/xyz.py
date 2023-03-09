import os
import string
from serial import Serial
import serial.tools.list_ports
from multiprocessing import Process
import threading
from time import sleep
import re
import numpy as np

# Soft limits
#x1 = -2
#y1 = -2
#x2 = -91
#y2 = -34
x1 = 0
y1 = 0
z1 = 0
x2 = -200
y2 = -75
z2 = -45

def which(iterable, obj):
    are = []
    for i,n in enumerate(iterable):
        if n == obj:
            are.append(n)
    return are

# Identify relevant well to well distances for 24, 48, 96 and 384 well plates and corresponding x_wells
well_dists = {6:18, 8:13, 12:9, 24:4.5}
yLabs = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P'] 
def gen_xy_old(xy1, xWells, yWells):
    '''
    Function for generating coordinates for a given plate size, based on the
    first coordinate.
    '''
    well_dist = well_dists[xWells]

    positions = []
    for i in range(yWells):
        for j in range(xWells):
            x = round((j*well_dist) + xy1[0], 2)
            y = round((-i*well_dist) + xy1[1], 2)
            z = round(np.random.random(), 2)
            labels = yLabs[i]+str(j+1)
            positions.append((x,y,z,labels))

    return positions


def gen_xy(xy1, position_list):
    x,y,z,_ = xy1

    new_positions = []
    for pos in position_list:
        X = x + pos[0]
        Y = y + pos[1]
        Z = z + pos[2]
        label = pos[3]

        new_positions.append((X, Y, Z, label))

    return new_positions

class Coordinates:
    def __init__(self):
        self.xs = []
        self.ys = []
        self.zs = []
        self.labels = []
        self.current = (0,0,0,'')

    def add(self, x, y, z, label):
        in_x, in_y, in_z, in_labs = (False, False, False, False)

        if x in self.xs: in_x = True
        if y in self.ys: in_y = True
        if z in self.zs: in_z = True
        if label in self.labels: in_labs = True

        if in_x and in_y and in_z and in_labs:
            return 
        else:
            self.xs.append(x)
            self.ys.append(y)
            self.zs.append(z)
            self.labels.append(label)

    def index(self, x, y, z=None, label=None):
        if z and label:
            coord_data = [(x,y,z,label) for x,y,z,label in zip(self.xs, self.ys, self.zs, self.labels)]
        else:
            if not z and not label:
                coord_data = [(x,y) for x,y in zip(self.xs, self.ys)]
            else:
                if z and not label:
                    coord_data = [(x,y,z) for x,y,z in zip(self.xs, self.ys, self.zs)]
                elif not z and label:
                    coord_data = [(x,y,label) for x,y,label in zip(self.xs, self.ys, self.labels)]

        vals = [n for n in [x,y,z,label] if n is not None]
        return coord_data.index(tuple(vals))

    def remove(self, x, y, z, label):            
        self.xs.remove(x)
        self.ys.remove(y)
        self.zs.remove(z)
        self.labels.remove(label)

    def update(self, x, y, z, label):
        l_ind = self.labels.index(label)
        self.xs[l_ind] = x
        self.ys[l_ind] = y
        self.zs[l_ind] = z

    def set_current(self, x, y, z, label):
        self.current = (x,y,z,label)

    def get_current(self):
        return self.current

class StageHardware:
    def __init__(self, xyz_port, joystick_port):
        self.xyz = Serial(xyz_port, 115200)
        self.joystick = Serial(joystick_port, 115200)

        self.joystickProc = None

    def initialiseXYZ(self):
        '''
        Setup parameters for Minitronics.
        '''
        self.xyz.timeout = 0.3
        
        # Initiate steppers
        self.xyz.write(str.encode('M17'+ '\n'))
        # GRBL...
        # Enable hard limits
        #self.xyz.write(str.encode('$21=1'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Enable homing
        #self.xyz.write(str.encode('$22=1'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Enable homing
        #self.xyz.write(str.encode('$22=1'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Correct homing cycle axis direction prior to homing
        #self.xyz.write(str.enc1ode('$23=0'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Reverse Z-axis direction prior to homing
        #self.xyz.write(str.encode('$3=4'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Switch to absolute coordinates after homing
        #self.xyz.write(str.encode('G90' + '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Steps per mm for X-axis
        #self.xyz.write(str.encode('$100=80'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Steps per mm for Y-axis
        #self.xyz.write(str.encode('$101=80'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Acceleration..
        #self.xyz.write(str.encode('$120=10'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        #self.xyz.write(str.encode('$121=10'+ '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # Prevent steppers from powering down - i.e. postition is fixed.
        #self.xyz.write(str.encode('$1=255' + '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))
        # # Switch to absolute coordinates after homing
        #self.xyz.write(str.encode('G90' + '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))

        print('XYZ stage setup complete')

    def setOrigin(self):
        '''
        Establish origin of stage.
        '''
        
        # Minitronics board
        # Begin homing
        self.xyz.write(str.encode('G28'+ '\n'))
        
        ## GRBL homing..
        #self.xyz.write(str.encode('$X'+ '\n')) # disable alarm lock
        #print(str(self.xyz.read_until('ok\r\n')))

        #self.xyz.write(str.encode('$H'+ '\n')) # initiate homing cycle
        #print(str(self.xyz.read_until('ok\r\n')))

        #  Edit: Report status
        #self.xyz.write(str.encode('$10=19' + '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))

        #self.xyz.write(str.encode('?' + '\n'))
        #print(str(self.xyz.read_until('ok\r\n')))

        #out = self.xyz.readline()
        #print(out)

        #self.moveXY(-4, -4, 0) # Shift the stage back inwards before permitting user input

        #  End of edits
        #out = self.xyz.readline()
        #return str(out)

    def moveXY(self, x, y, z):
        '''
        Move to absolute X and Y and Z coordinates
        '''
        # Round up
        x = round(x, 2)
        y = round(y, 2)
        z = round(z, 2)
        
        # Minitronics board
        self.xyz.write(str.encode(f'G0 X{x} Y{y} Z{z}\n'))       
        print('Sending: ' + str(f'G0 X{x} Y{y} Z{z}\n'))
        
    def moveXY_from_relative_coords(self, x, y, z):
        '''
        Move to absolute X and Y ad Z coordinates
        '''
        # Round up
        x = round(x, 2)
        y = round(y, 2)
        z = round(z, 2)
        
        curr_x, curr_y, curr_z = self.grabXY()
        x = curr_x + x
        y = curr_y + y
        z = curr_z + z
        # Minitronics board
        self.xyz.write(str.encode(f'G0 X{x}Y{y}Z{z}\n'))       
        print('Sending: ' + str(f'G0 X{x}Y{y}Z{z}\n'))
        
                
        ##GRBL
        #self.xyz.write(str.encode(f'G00 X{x}Y{y}Z{z}\n'))
        #ret = str(self.xyz.read_until('ok\r\n'))

        # For debug purposes..
        #print('Sending: ' + str(f'G00 X{x}Y{y}Z{z}\n'))
        #out = self.xyz.readline()
        # if 'error' in str(out):
        #     return str('Error - check XYZ stage and recalibrate')
        # else:
        #     return str('Grbl "$" system command was not recognized or supported')
        #return ret

    def grabXY(self):
        '''Retrieves the current xyz stage position.'''
        
        # Minitronics board
        self.xyz.write(str.encode('M114' + '\n'))
        bts = self.xyz.inWaiting()
        out = self.xyz.read(bts)
        sleep(0.5)
        
        #self.xyz.write(str.encode('M114' + '\n'))
        #bts = self.xyz.inWaiting()
        #out = self.xyz.read(bts)
        #Minitronics serial output is messy so requires cleaning up.
        remove = '\XYZE:"\'' + string.ascii_lowercase
        table = str.maketrans('','',remove)
        out = str(out).translate(table)
        print(out)
        try:
            out = out.split(' ')[0:3] # remove the E value.
            print('XYZ: ', str(out))
            #x,y,z = out[0], out[1], out[2]
            x,y,z = map(float, out)
            coords = x,y,z
        except:
            raise
        
        return coords
    
        ## GRBL
        #self.xyz.write(str.encode('?' + '\n'))
        #bts = self.xyz.inWaiting()
        #out = self.xyz.read(bts)
        #sleep(0.5)
        
        # Read position
        #self.xyz.write(str.encode('?' + '\n'))
        #bts = self.xyz.inWaiting()
        #out = self.xyz.read(bts)
        #print(bts, out)
        #try:
        #    out = out.decode().split('|')[1].split(':')[1].split(',')
        #    x,y,z = map(float, out)
        #    coords = x,y,z
        #except:
        #    raise
        
        #return coords

    #@staticmethod
    def get_manual_control_xy(self, mv):
        try:
            print(mv)
            # Remove G1
            xy = mv[2:]
            #print('Received from joystick: ' + str(xy))
            f_val = xy[xy.index('F')::]
            #print(f_val)
            f_val = re.sub('F','',f_val)
        
            #xy = mv[9:-(len(mv) - mv.index('F'))]
            #print('xy:', xy)
        
            if_x = 'X' in xy
            if_y = 'Y' in xy
            if_z = 'Z' in xy
            
            #print(if_x, if_y, if_z)

            x_val = 0
            y_val = 0
            z_val = 0
            
            if if_x and if_y:
                x_ind = xy.index('X')
                y_ind = xy.index('Y')
                f_ind = xy.index('F')
                x_val = float(xy[x_ind+1:y_ind])
                y_val = float(xy[y_ind+1:f_ind])
                #print(x_val, y_val)
            elif if_x and not if_y:
                x_ind = xy.index('X')
                f_ind = xy.index('F')
                x_val = float(xy[x_ind+1:f_ind])
                #print(x_val)
            elif not if_x and if_y:
                y_ind = xy.index('Y')
                f_ind = xy.index('F')
                y_val = float(xy[y_ind+1:f_ind])
                #print(y_val)
            elif if_z:
                z_ind = xy.index('Z')
                f_ind = xy.index('F')
                z_val = float(xy[z_ind+1:f_ind])
                print(z_val)
            #print('fn returning: ', x_val, y_val, z_val)
            #print('X:' + x_val, y_val, z_val)
               
            return x_val, y_val, z_val, f_val
        except:
            print(True)
            return 0, 0, 0, 0
        
    def _readJoystick(self):
        '''
        Monitor serial from joystick and pass on to the xyz stage.
        '''
        self.ix, self.iy, self.iz = self.grabXY()
        #print(self.ix, self.iy, self.iz)
        while True:
            self.joystick.inWaiting()
            js_mv = self.joystick.readline()
            js_mv = js_mv.decode()
            #print('js_mv: ' + str(js_mv))
            if 'joystick' in js_mv:
                continue
            
            x_mv, y_mv, z_mv, f_val = self.get_manual_control_xy(js_mv)
                
            #print(x_mv, y_mv, z_mv, f_val)
            
            x_mv = x_mv / 2
            y_mv = y_mv / 2
            z_mv = z_mv
            
            temp_x = self.ix + x_mv
            temp_y = self.iy + y_mv
            temp_z = self.iz + z_mv
            
            temp_x = round(temp_x, 4)
            temp_y = round(temp_y, 4)
            temp_z = temp_z
            #temp_z = round(temp_z, 2)
                
            #print(temp_x, temp_y, temp_z)

            stop_x = False
            stop_y = False
            stop_z = False
            if temp_x >= x1 or temp_x <= x2:
                stop_x = True
            if temp_y >= y1 or temp_y <= y2:
                stop_y = True
            if temp_z >= z1 or temp_z <= z2:
                stop_z = True
                
            #print(stop_x, stop_y, stop_z)
            
            to_move = False
            js_mv_new = 'G0'
            for i,a,mv,curr in zip(
                    ['X', 'Y', 'Z'],
                    [stop_x, stop_y, stop_z],
                    [temp_x, temp_y, temp_z],
                    ['ix', 'iy', 'iz']
                ):
                
                if not a:
                    to_move = True
                    js_mv_new += f' {i}{mv}'
                    setattr(self, curr, mv)                    
                    
            js_mv_new += f' F{f_val}\n'
            if not to_move:
                js_mv_new = None
                
#             #f_mv = js_mv[js_mv.index('F'):]
#             if not stop_x and not stop_y and not stop_z:
#                 js_mv_new = f'G0 X{temp_x} Y{temp_y} Z{temp_z} F{f_val}\n'                
#                 ix = temp_x
#                 iy = temp_y               
#             elif stop_x and not stop_y and not stop_z:
#                 js_mv_new = f'G0 Y{temp_y} Z{temp_z} F{f_val}\n'
#                 #js_mv_new = f'$J=G21G91Y{y_mv}{f_mv}'
#                 iy = temp_y
#             elif not stop_x and stop_y and not stop_z:
#                 js_mv_new = f'G0 X{temp_x} Z{temp_z} F{f_val}\n'
#                 #js_mv_new = f'$J=G21G91X{x_mv}{f_mv}'
#                 ix = temp_x
#             elif stop_x and stop_y and not stop_z:
#                 js_mv_new = f'G0 Z{temp_z} F{f_val}\n'
#                 #js_mv_new = f'$J=G21G91X{x_mv}{f_mv}'
#                 iz = temp_z
#             ## Not finished - need the various combos above, although joystick and buttons
#             ## almost impossible to use together..
#             elif stop_x and stop_y and stop_z:
#                 js_mv_new = None
#         
            #print(js_mv_new)

            if js_mv_new is not None:
                #print(str('sending: '), js_mv_new)
                # Round up
                self.xyz.write(str.encode(js_mv_new))
                self.joystick.flushInput()
                self.xyz.flushInput()

                # print('js: ' + str(self.joystick.in_waiting))
                # print('js: ' + str(self.joystick.out_waiting))
                # print('xy: ' + str(self.xyz.reset_input_buffer()))
                # print('xy: ' + str(self.xyz.out_waiting))
            #print(ix, iy, iz)
            sleep(0.00001)

    def launchJoystick(self):
        '''
        Launch a process to monitor the joystick (via _readJoystick() reading from an Arduino 
        running joystick.ino).
        '''
        self.joystickProc = Process(target=self._readJoystick)
        self.joystickProc.start()

    def disableJoystick(self):
        '''Method to disable joystick process. '''
        if self.joystickProc is not None:
            self.joystickProc.terminate()

    def close(self):
        if self.xyz:
            self.xyz.close()
        if self.joystick:
            self.joystick.close()

if __name__ == '__main__':
    stage = StageHardware('/dev/ttyACM2', '/dev/ttyACM0')
    stage.initialiseXYZ()
    stage.setOrigin()
    
    sleep(10)
      
    stage.moveXY_from_relative_coords(-10, -10, 0)
    sleep(5)
    print(stage.grabXY())
    sleep(2)
    
    stage.launchJoystick()

        