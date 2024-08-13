import os
import string
from serial import Serial
import serial.tools.list_ports
from multiprocessing import Process
import threading
from time import sleep
import time
import re
import numpy as np
import ujson
from more_itertools import pairwise

def which(iterable, obj):
    are = []
    for i,n in enumerate(iterable):
        if n == obj:
            are.append(n)
    return are

# Identify relevant well to well distances for 24, 48, 96 and 384 well plates and corresponding x_wells
well_dists = {6:19, 8:13.5, 12:9, 24:4.4}
yLabs = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P'] 
def gen_xy_old(xy1, xWells, yWells):
    '''
    Function for generating coordinates for a given plate size, based on the
    first coordinate.
    '''
    well_dist = well_dists[xWells]

    positions = []
    for i in range(yWells):
        row_positions = []
        for j in range(xWells):
            x = round((j*well_dist) + xy1[0], 2)
            y = round((i*well_dist) + xy1[1], 2)
            z = xy1[2]
            labels = yLabs[i]+str(j+1)
            row_positions.append((x,y,z,labels))

        if i % 2 != 0:
            row_positions = row_positions[::-1]

        positions.extend(row_positions)

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


def check_scan_time(positions):
    fspeed = 2.5

    scan_time = 0

    for prev, next_ in pairwise(positions):
        x1,y1,z1,l = prev
        x2,y2,z2,l = next_

        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
        wait = dist / fspeed
        scan_time += wait+1

    return scan_time


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
        self.xyz = xyz_port
        self.joystick = joystick_port
        self.fspeed = 2.5 # mm s-1
        
        self.joystickProc = None
        self.initialiseXYZ()

    def initialiseXYZ(self):
        '''
        Setup parameters for Minitronics.
        '''
        self.xyz.timeout = 0.3
        
        # Initiate steppers
        self.xyz.write(str.encode('M17'+ '\n'))

        print('XYZ stage setup complete')

    def setOrigin(self):
        '''
        Establish origin of stage.
        '''        
        # Begin homing
        self.xyz.write(str.encode('G28'+ '\n'))
        self.wait_until()
                    
    def wait_until(self):
        '''
        Wait until stage is idle.
        '''
        while True:
            try:
                status = self.check_status()
            except Exception as e:
                status = None
                pass
            
            if status != 'I':
                time.sleep(1)
                continue
            else:
                break
                
    def wait_distance(self, prev, next_): # Must be in mm
        x1,y1,z1 = prev
        x2,y2,z2 = next_

        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
        wait = dist / self.fspeed
        time.sleep(wait)

    def check_status(self):
        self.xyz.write(str.encode('M408 S0'+ '\n'))
        bts = self.xyz.inWaiting()
        out = self.xyz.read(bts)
        
        if 'status' not in out.decode():
            return None
        
        status = eval(str.split(out.decode(), '\n')[0])['status']
        return status        
        
    def moveXY(self, x, y, z):
        '''
        Move to absolute X and Y and Z coordinates
        '''
        # Round up
        x = round(x, 2)
        y = round(y, 2)
        z = round(z, 2)
        
        self.xyz.write(str.encode(f'G0 X{x}Y{y}Z{z}F1000\n'))       
        print('Sending: ' + str(f'G0 X{x}Y{y}Z{z}F1000\n'))
        self.wait_distance(self.grabXY(), (x,y,z))
        self.wait_until()
        time.sleep(1)

    def moveXY_from_relative_coords(self, x, y, z):
        '''
        Move to relative X and Y and Z coordinates
        '''
        # Round up
        x = round(x, 2)
        y = round(y, 2)
        z = round(z, 2)
        
        curr_x, curr_y, curr_z = self.grabXY()
        x = curr_x + x
        y = curr_y + y
        z = curr_z + z

        self.xyz.write(str.encode(f'G0 X{x}Y{y}Z{z}F1000\n')) # Feed rate of 1000 for fast movement on Duet3D board    
        print('Sending: ' + str(f'G0 X{x}Y{y}Z{z}F1000\n'))
        
        self.wait_until()
        
    def grabXY(self):
        '''Retrieves the current xyz stage position.'''

        # First read to clear buffer
        self.xyz.write(str.encode('M114' + '\n'))
        bts = self.xyz.inWaiting()
        out = self.xyz.read(bts)                  

        coords = None
        for i in range(10):
            # Second read to clear buffer
            self.xyz.write(str.encode('M114' + '\n'))
            bts = self.xyz.inWaiting()
            out = self.xyz.read(bts)

            remove = '\XYZE:"\'' + string.ascii_lowercase
            table = str.maketrans('','',remove)
            out = str(out).translate(table)
            
            try:
                out = out.split(' ')[0:3] # remove the E value.
                x,y,z = map(float, out)
                coords = x,y,z
                print('XYZ: ', coords)
                break
            except:
                pass
            
            time.sleep(0.2)

        if not coords:
            raise SystemError('Unable to retrieve position from Duet3D board.')
        
        return coords
    
    #@staticmethod
    def get_manual_control_xy(self, mv):
        try:
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
            #print('fn returning: ', x_val, y_val, z_val)
            #print('X:' + x_val, y_val, z_val)
               
            return x_val, y_val, z_val, f_val
        except:
            print(True)
            return 0, 0, 0, 0
        
    def _readJoystick(self, current_pos):
        '''
        Monitor serial from joystick and pass on to the xyz stage.
        '''
        self.ix, self.iy, self.iz = current_pos
        
        while True:
            self.joystick.inWaiting()
            js_mv = self.joystick.readline()
            js_mv = js_mv.decode()
            #print('js_mv: ' + str(js_mv))
            if 'joystick' in js_mv:
                continue
            
            x_mv, y_mv, z_mv, f_val = self.get_manual_control_xy(js_mv)
                
            print(x_mv, y_mv, z_mv, f_val)
            
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
                
            stop_x = False
            stop_y = False
            stop_z = False
            
            if temp_x <= x1 or temp_x >= x2:
                stop_x = True
            if temp_y <= y1 or temp_y >= y2:
                stop_y = True
            if temp_z <= z1 or temp_z >= z2:
                stop_z = True
                
#             print(stop_x, stop_y, stop_z)
            
            to_move = False
            js_mv_new = 'G0 '
            for i,a,mv,curr in zip(
                    ['X', 'Y', 'Z'],
                    [stop_x, stop_y, stop_z],
                    [temp_x, temp_y, temp_z],
                    ['ix', 'iy', 'iz']
                ):
                
                if not a:
                    to_move = True
                    js_mv_new += f'{i}{mv}'
                    setattr(self, curr, mv)                    
                    
            js_mv_new += f'F{f_val}\n'
            if not to_move:
                js_mv_new = None
                
            if js_mv_new is not None:
                print(js_mv_new)
                self.xyz.write(str.encode(js_mv_new))
                self.joystick.flushInput()
                self.xyz.flushInput()

                # print('js: ' + str(self.joystick.in_waiting))
                # print('js: ' + str(self.joystick.out_waiting))
                # print('xy: ' + str(self.xyz.reset_input_buffer()))
                # print('xy: ' + str(self.xyz.out_waiting))
            #print(ix, iy, iz)
            sleep(0.0001)

    def launchJoystick(self):
        '''
        Launch a process to monitor the joystick (via _readJoystick() reading from an Arduino 
        running joystick.ino).
        '''
        self.disableJoystick()
        
        self.joystickProc = Process(target=self._readJoystick, args=(self.grabXY(),))
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
    import matplotlib.pyplot as plt

    positions = gen_xy_old((10,10,0), 12, 8)
    print(check_scan_time(positions))

    for i, (x,y,z,l) in enumerate(positions):
        plt.plot(x, y, 'o')
        plt.text(x,y,s=f'{l}_{i}')

    plt.show()

    # stage = StageHardware(Serial('/dev/ttyACM1', 115200), None)
    # stage.setOrigin()
    
    # sleep(2)
    
    # for i in range(100):
    #     for x in range(1, 150, 10):
    #         for y in range(1, 80, 10):
    #             stage.moveXY(210-x,0+y,0)
 
        
    # stage.moveXY_from_relative_coords(-30, 30, 0)
#     stage.moveXY_from_relative_coords(-15, 15, 0)
#     stage.moveXY_from_relative_coords(-15, 0, 0)
#     stage.moveXY_from_relative_coords(25, -20, 0)
#     print(stage.grabXY())
#     sleep(2)
#  
#     stage.setOrigin()
#     
#     sleep(10)
#       
#     stage.moveXY_from_relative_coords(-10, 10, 0)
#     sleep(2)
#     stage.moveXY_from_relative_coords(-15, 15, 0)
#     sleep(2)
#     stage.moveXY_from_relative_coords(-15, 0, 0)
#     sleep(2)
#     stage.moveXY_from_relative_coords(25, -20, 0)
#     sleep(2)
#     print(stage.grabXY())
#     sleep(2)
    
# 
#     stage.launchJoystick()
#     sleep(10)

        
