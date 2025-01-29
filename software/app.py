#!/usr/bin/python

# System wide imports
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import cv2
import gc
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import subprocess
import multiprocessing as mp
import time as timelib
import shutil
import base64
import os
import signal
import json
import glob
import re
import time
import numpy as np
from natsort import natsorted, ns
import pandas as pd
from serial.tools import list_ports
import serial
from tqdm import tqdm
from flask import request, Flask, Response
from tempfile import TemporaryDirectory
import smtplib
import datetime
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
import pwd
import vuba
from collections import deque
from tkinter import filedialog
from tkinter import *
import tkfilebrowser
import psutil

## Diskcache
import diskcache

if os.path.exists('./cache'):
    shutil.rmtree('./cache')

cache = diskcache.Cache('./cache')
long_callback_manager = DiskcacheLongCallbackManager(cache)

# App specific modules
import layout
import camera_backend_picamera2
import renderers
import emails
import leds
import xyz
from acquisition import Acquisition

# Simple low-level functions 
def all(iterable, obj):
    not_ = []
    for i in iterable:
        if i is not obj:
            not_.append(i)

    if not_:
        return False
    else:
        return True

def any(iterable, obj):
    is_ = False
    for i in iterable:
        if i is obj:
            is_ = True
            break
    return is_

def check_port(port, queue):
    port = serial.Serial(port, 115200)
    time.sleep(1)

    out = str(port.readline())
    
    if 'light' in out:
        queue.put('light')
    else:
        queue.put('stage')

def check_devices():
    ports = list_ports.grep('/dev/ttyACM*')
    names = [p.device for p in ports]

    led_port = None
    xyz_port = None
    
    for p in names:
        queue = mp.Queue()
        proc = mp.Process(target=check_port, args=(p, queue))
        proc.start()
        
        time.sleep(2)
        if queue.empty():
            xyz_port = p
        else:
            port_type = queue.get()
            if 'light' in port_type:
                led_port = p

        queue.close()

    print(led_port, xyz_port)
    return led_port, xyz_port

# Source: https://gist.github.com/IdeaKing/11cf5e146d23c5bb219ba3508cca89ec
def resize_with_pad(image, new_shape, padding_color=(0,0,0)):
    """Maintains aspect ratio and resizes with padding.
    Params:
        image: Image to be resized.
        new_shape: Expected (width, height) of new image.
        padding_color: Tuple in BGR of padding color
    Returns:
        image: Resized image with padding
    """
    original_shape = (image.shape[1], image.shape[0])
    ratio = float(max(new_shape))/max(original_shape)
    new_size = tuple([int(x*ratio) for x in original_shape])
    image = cv2.resize(image, new_size)
    delta_w = new_shape[0] - new_size[0]
    delta_h = new_shape[1] - new_size[1]
    top, bottom = delta_h//2, delta_h-(delta_h//2)
    left, right = delta_w//2, delta_w-(delta_w//2)
    image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=padding_color)
    return image

def gen(camera, camera_settings):
    while True:
        if camera_state.trigger:

            exposure = camera_settings.settings['exposure']
            fps = camera_settings.settings['framerate']
            sensor_mode = camera_settings.settings['sensor_mode']
            analogue_gain = camera_settings.settings['analogue_gain']

            if camera_state.state == 'streaming':
                with camera_backend_picamera2.VideoGenerator(camera, exposure, fps, analogue_gain, sensor_mode) as cap_gen:
                    for frame in cap_gen:
                        if camera_state.trigger:
                            frame = resize_with_pad(frame, (640, 480))
                            frame = camera_backend_picamera2.frame_to_bytes(frame)
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                        else:
                            break
        else:
            time.sleep(0.1)

class UserInputStore:
    def __init__(self):
        self.parameters = dict(
            # Camera values
            led_value=None,
            exposure=None,
            contrast=None,
            fps=None,
            resolution_key=None,

            # Acquisition values
            pos_number=None,
            timepoints=None,
            interval=None,
            length=None,
            path=None
        )

        self.initial_values = {k:v for k,v in self.parameters.items()}
        self.update_num = 0

    def set(self, **kwargs):
        if self.update_num == 0:
            for key, value in kwargs.items():
                self.initial_values[key] = value
                self.parameters[key] = value
        else:
            for key, value in kwargs.items():
                if value != self.initial_values[key]:
                    print(True, value, self.initial_values[key])
                    self.parameters[key] = value

        self.update_num += 1

    def get(self, *args):
        return [self.parameters[k] for k in args]

        
# Acquisition state for disabling other components whilst acquisition is running
class AcquisitionState:
    def __init__(self):
        self.running = False

    def started(self):
        self.running = True

    def finished(self):
        self.running = False

# Camera state for remote-view
class CameraState:
    def __init__(self):
        self.trigger = False
        self.state = None

    def on_off(self, state):
        self.state = state
        if self.trigger:
            self.trigger = False
        else:
            self.trigger = True

class CameraConfigLoad:
    # Only used as backend store for camera settings loaded through config file
    def __init__(self):
        self.exposure = None
        self.width = None
        self.height = None
        self.sensor_mode = None
        self.framerate = None

class ExperimentJobLog:
    def __init__(self):
        self.log = {}
        self.current = dict(replicate=None, timepoint=None)

    def startup(self, replicates, timepoints):
        for r in replicates:
            self.log[r] = dict(
                timepoint=[t for t in list(range(timepoints))],
                acq_time=[None for i in range(timepoints)]
            )

    def update(self, replicate, timepoint, dt):
        self.log[replicate]['acq_time'][timepoint] = dt
        self.current['replicate'] = replicate
        self.current['timepoint'] = timepoint

    def clear(self):
        self.log = {}

    def export(self, file):
        df = dict(replicate=[], timepoint=[], date_time=[])

        for key, item in self.log.items():
            tp = item['timepoint']
            dt = item['acq_time']
            replicate = [key for i in tp]

            df['replicate'].extend(replicate)
            df['timepoint'].extend(tp)
            df['date_time'].extend(dt)

        df = pd.DataFrame(data=df)
        df.to_csv(file)

class RelativeXYZ:
    def __init__(self, axis_limits):
        self.x = None
        self.y = None
        self.z = None

        xl, yl, zl = axis_limits

        # Limits
        self.x1, self.x2 = xl
        self.y1, self.y2 = yl
        self.z1, self.z2 = zl

    def start(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def update(self, x=0, y=0, z=0):
        u_x = self.x + x
        if u_x >= self.x1 and u_x <= self.x2:
            self.x += x
            
        u_y = self.y + y
        if u_y >= self.y1 and u_y <= self.y2:
            self.y += y
            
        u_z = self.z + z
        if u_z >= self.z1 and u_z <= self.z2:
            self.z += z
            
        print(self.x,self.y,self.z)


picam2 = camera_backend_picamera2.Camera()

led_port, xyz_port = check_devices()
sensor_modes = picam2.get_sensor_modes()

# Initiate serial connections
led_serial = serial.Serial(led_port, 115200)
xyz_serial = serial.Serial(xyz_port, 115200)

camera_state = CameraState()
camera_settings = camera_backend_picamera2.CameraSettings()
live_stream = camera_backend_picamera2.LiveStream(picam2.camera)

experimental_log = ExperimentJobLog()
acquisition = Acquisition()
stage = xyz.StageHardware(xyz_serial, None)
coord_data = xyz.Coordinates()
leds = leds.HardwareBrightness(led_serial)
loaded_camera_settings = CameraConfigLoad() 
acquisition_state = AcquisitionState()
user_input_store = UserInputStore()

relative = RelativeXYZ(stage.get_axis_limits())

server = Flask(__name__)
app = dash.Dash(__name__, server=server, long_callback_manager=long_callback_manager, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/app.css', dbc.icons.FONT_AWESOME])
app.config['suppress_callback_exceptions'] = True 
app.layout = layout.app_layout(sensor_modes)
# app.css.append_css({'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'})

# For callbacks where no return is needed
trigger = ''

# =============================================================================================== #
# ------------------------------------ Acquire tab callbacks ------------------------------------ #
# =============================================================================================== #

with open('./app_config.json', 'r') as conf:
    app_conf = json.load(conf)
    emails_on = app_conf['emails']

email = emails.Emails()
if emails_on == 'on':
    email.login(app_conf['email_username'], app_conf['email_password'])
    timelib.sleep(1)
email.close()

# ------------------ Html rendering callbacks ----------------- #
# ============================================================= #
@app.callback(
    output=Output('exposure', 'value'),
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_exposure_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        exposure = camera_settings.get('exposure') / 1000 # For ms on pi
    else:
        exposure = loaded_camera_settings.exposure / 1000 # For ms on pi
    return exposure

@app.callback(
    output=Output('analogue_gain', 'value'),
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_analogue_gain_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        analogue_gain = camera_settings.get('analogue_gain') # For ms on pi
    else:
        analogue_gain = loaded_camera_settings.analogue_gain # For ms on pi
    return analogue_gain

@app.callback(
    output=[Output('resolution-preset', 'value')],
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_resolution_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        mode = camera_settings.get('sensor_mode')
        return [mode]
    else:
        mode = loaded_camera_settings.sensor_mode
        return [mode]

@app.callback(
    output=[
        Output('fps', 'value'),
        Output('fps', 'min'),
        Output('fps', 'max')
    ],
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children'),
        Input('resolution-preset', 'value'),
        Input('exposure', 'value')
    ])
def update_fps_ui(cam_init, loaded_data, mode, exposure):
    sensor_mode = sensor_modes[mode]
    min_fps = 1
    max_fps = round(sensor_mode['fps'])
    max_fps_at_exp = round(1 / ((exposure*1000) / 1e6))
    fps_range = (min_fps, max_fps if max_fps_at_exp > max_fps else max_fps_at_exp)
        
    if trigger not in [loaded_data]:
        fps = camera_settings.get('framerate')       
    else:
        fps = loaded_camera_settings.framerate
    return (fps if fps < fps_range[1] else fps_range[1], *fps_range)  


# ============================================================= #
# ------------------ Updating UI callbacks -------------------- #
# ============================================================= #

@app.callback(
    output=Output('hardware-brightness-callback', 'children'),
    inputs=[Input('hardware-brightness', 'value')])
def update_hardware_brightness(value):
    leds.set(value)

@app.callback(
    output=Output('hidden-update-callback', 'children'),
    inputs=[Input('update-camera-settings', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('exposure', 'value'),
        State('resolution-preset', 'value'),
        State('fps', 'value'),
        State('analogue_gain', 'value')
    ])
def update_camera_settings(n_clicks, cam_init, exposure, resolution, fps, analogue_gain):
    if n_clicks:
        camera_settings.set('exposure', exposure * 1000) # Convert back to exposure units on pi
        camera_settings.set('sensor_mode', resolution)
        camera_settings.set('framerate', fps)
        camera_settings.set('analogue_gain', analogue_gain)
        return trigger  
    else:
        return dash.no_update

@server.route('/video_feed')
def video_feed():
    return Response(gen(picam2.camera, camera_settings),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

class TabState:
    state = 'still-tab'

@app.callback(
    output=[
        Output('camera-state-live-view', 'children'),
        Output('image-capture-tab-state-stream', 'children'),
        Output('streaming-spinner', 'children')
    ],
    inputs=[Input('camera-live-stream', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('camera-streaming-mode', 'value')]
)
def start_stop_live_view(n_clicks, cam_init, mode):
    if n_clicks is not None:
        if (camera_state.trigger and camera_state.state == 'streaming'):
            camera_state.on_off('streaming')
            return trigger, trigger, None
        elif live_stream.is_streaming:
            live_stream.stop()
            return trigger, trigger, None
        else:
            # Desktop ----
            if mode:
                TabState.state = 'stream-tab'

                exposure = camera_settings.settings['exposure']
                fps = camera_settings.settings['framerate']
                sensor_mode = camera_settings.settings['sensor_mode']
                analogue_gain = camera_settings.settings['analogue_gain']
                
                print('SENSOR_MODE', sensor_mode)
                
                live_stream.start(exposure, fps, analogue_gain, sensor_mode)
                return trigger, trigger, dbc.Spinner(color='primary', size='md')
            # Browser -----
            else:
                TabState.state = 'stream-tab'
                camera_state.on_off('streaming')
                return trigger, trigger, dbc.Spinner(color='primary', size='md')
    else:
        return dash.no_update, dash.no_update, trigger


@app.callback(
    output=[
        Output('camera-state-snapshot', 'children'),
        Output('still-image', 'children'),
        Output('image-capture-tab-state-still', 'children')
    ],
    inputs=[Input('test-frame-button', 'n_clicks')],
    state=[State('connect-cam-callback', 'children')])
def update_still_image(n_clicks, cam_init):
    if n_clicks is None:
        frame = cv2.imread('./assets/img/blankImg.png')
        frame = cv2.resize(frame, (640, 480))
        return dash.no_update, renderers.interactiveImage('snap-image', frame), dash.no_update
    else:
        if camera_state.trigger and camera_state.state == 'streaming':
            camera_state.on_off('streaming')
            time.sleep(0.5)
        elif live_stream.is_streaming:
            live_stream.stop()
            time.sleep(0.5)

        exposure = camera_settings.settings['exposure']
        fps = camera_settings.settings['framerate']
        sensor_mode = camera_settings.settings['sensor_mode']
        analogue_gain = camera_settings.settings['analogue_gain']

        frame = picam2.still_capture(exposure, fps, analogue_gain, sensor_mode)

        existing_images = glob.glob('./snap_images/snap-*.png')
        cv2.imwrite(f'./snap_images/snap-{len(existing_images)+1}.png', frame)

        TabState.state = 'still-tab'
        return trigger, renderers.interactiveImage('snap-image', frame), trigger


@app.callback(
    output=Output('image-capture-tabs', 'value'),
    inputs=[
        Input('image-capture-tab-state-stream', 'children'),
        Input('image-capture-tab-state-still', 'children')])
def update_tab_state(still_state, stream_state):
    return TabState.state

@app.callback(
    output=Output('total-wells', 'children'),
    inputs=[Input('xy_coords', 'data')])
def update_well_number(data):
    x = [d['x'] for d in data] # always will be filled
    return len(x)

@app.callback(
    output=[
        Output('acquire-path-input', 'value'),
        Output('acquisition-folder-name-popup', 'is_open')
    ],
    inputs=[Input('path-select', 'n_clicks')]
)
def get_acq_path(n_clicks):
    if n_clicks:
        root = Tk()
        folder_selected = tkfilebrowser.askopendirname(
            parent=root,
            title='Select an acquisition folder',
            okbuttontext='Open')
        root.destroy()

        if " " in folder_selected:
            return dash.no_update, True

        return folder_selected, False
    else:
        return dash.no_update, False

# @app.callback(
#     output=Output('drive-select', 'options'),
#     inputs=[Input('drive-refresh', 'n_clicks')]
# )
# def update_drive_select(n_clicks):
#     user = pwd.getpwuid(os.getuid()).pw_name
#     external_dir = os.path.join('/media', user)
#     disks = os.listdir(external_dir)
#     return [dict(label=d, value=d) for d in disks]

# @app.callback(
    # output=Output('acquire-outpath-check', 'children'),
    # inputs=[Input('acquire-path-input', 'value')])
# def check_acquire_path(path):
    # if path:
        # if os.path.exists(path):
            # return 'Folder already exists. Please name a new one.'
        # else:
            # return trigger
    # else:
        # return trigger

# @app.callback(
#     output=Output('disk_space_text', 'children'),
#     inputs=[Input('acquire-path-input', 'value')]
# )
# def disk_usage(path):
#     if path:
#         space = psutil.disk_usage(path)
#         free = space.free / float(1<<30) * 1.074
#         total = space.total / float(1<<30) * 1.074

#         return f'{round(free, 1)}GB / {round(total, 1)}GB'
#     else:
#         return dash.no_update

# @app.callback(
#     output=Output('disk_space_text', 'children'),
#     inputs=[
#         Input('acquire-path-input', 'value'),
#         State('total-time-points', 'value'),
#         State('each-time-limit', 'value'),
#         State('fps', 'value'),
#         State('acquisition-number', 'value')
#     ]
# )
# def acq_usage(path, timepoints, video_sec, fps, position_number):
#     if path:
#         space = psutil.disk_usage(path)
#         free = space.free / float(1<<30) * 1.074
#         total = space.total / float(1<<30) * 1.074

#         if position_number == 'Single':
#             frames = 

#         else:


#         return f'{free}GB / {total}GB'
#     else:
#         return dash.no_update

# ============================================================= #
# ------------------ Config load/save callbacks --------------- #
# ============================================================= #

@app.callback(
    output=Output('loaded-data-callback', 'children'),
    inputs=[Input('load-config-button', 'n_clicks')])
def upload_config(n_clicks):
    if n_clicks is None:
        return dash.no_update
    else:        
        root = Tk()
        filename = tkfilebrowser.askopenfilename(
            parent=root,
            initialdir='./configs',
            title='Select a config file',
            filetypes=[("Configs", "*.json"), ("All files", "*")],
            okbuttontext='Open'
        )
        root.destroy()

        with open(filename, 'r') as fp:
            data = json.load(fp)

            loaded_camera_settings.exposure = data['camera_settings']['exposure']
            loaded_camera_settings.framerate = data['camera_settings']['framerate']
            loaded_camera_settings.width = data['camera_settings']['width']
            loaded_camera_settings.height = data['camera_settings']['height']
            loaded_camera_settings.sensor_mode = data['camera_settings']['sensor_mode_ind']
            loaded_camera_settings.analogue_gain = data['camera_settings']['analogue_gain']

            coord_data.xs = data['positions']['x_coordinates']
            coord_data.ys = data['positions']['y_coordinates']
            coord_data.zs = data['positions']['z_coordinates']
            coord_data.labels = data['positions']['labels']

        return trigger

@app.callback(
    output=Output('config-save-callback', 'children'),
    inputs=[Input('save-config-button', 'n_clicks')],
    state=[
        State('exposure', 'value'),
        State('fps', 'value'),     
        State('resolution-preset', 'value'),
        State('analogue_gain', 'value'),
        State('total-time-points', 'value'),
        State('acq-length', 'value'),
        State('each-time-limit', 'value'),
        State('acquire-path-input', 'value'),
    ])
def save_config(n_clicks, exposure, fps, resolution, analogue_gain, timepoints, interval, length, path):
    if n_clicks is None:
        return dash.no_update
    else:
        root = Tk()
        filename = tkfilebrowser.asksaveasfilename(
            parent=root,
            initialdir='./configs',
            title='Save a config file',
            filetypes=[("Configs", "*.json"), ("All files", "*")],
            okbuttontext='Save'
        )
        root.destroy()

        width, height = sensor_modes[resolution]['size']

        featureDict = {
            'camera_settings': {
                'exposure': exposure * 1000, # Convert back to exposure units on pi
                'framerate': fps,
                'width': width,
                'height': height,
                'sensor_mode_ind': resolution,
                'analogue_gain': analogue_gain
            },
            'positions': {
                'x_coordinates': coord_data.xs,
                'y_coordinates': coord_data.ys,
                'z_coordinates': coord_data.zs,
                'labels': coord_data.labels
            },
            'experiment_settings': {
                'timepoints': timepoints,
                'interval': interval,
                'capture_length': length,
                'output_path': path
            }
        }

        if not filename.endswith('.json'):
            filename = f'{filename}.json'

        with open(filename, 'w') as fp:
            json.dump(featureDict, fp, indent=4)

# ============================================================= #
# ------------------ Acquisitions callbacks ------------------- #
# ============================================================= #
@app.callback(
    output=[
        Output('acquisition_state', 'children'),
        Output('acquisition-live-stream-popup', 'is_open'),
        Output('acquisition-folder-popup', 'is_open'),
        Output('acquisition-interval-popup', 'is_open')],
    inputs=[Input('acquire-button', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('total-time-points', 'value'),
        State('acq-length', 'value'),
        State('each-time-limit', 'value'),
        State('exposure', 'value'),
        State('fps', 'value'),     
        State('resolution-preset', 'value'),
        State('analogue_gain', 'value'),
        State('acquire-path-input', 'value'),
        State('xy_coords', 'data'),
        State('acquisition-number', 'value'),
        State('light-auto-dimming', 'value')
    ],
)
def acquire(n_clicks, cam_init, timepoints, length, time, exposure, fps, resolution, analogue_gain, user_path, xy_data, acq_num, light_auto_dim):
    if n_clicks is None:
        return trigger, False, False, False
    else:
        if len(os.listdir(user_path)):
            return trigger, False, True, False

        if camera_state.trigger and camera_state.state == 'streaming':
            print('Streaming currently, will fail...')
            return trigger, True, False, False

        camera_scan_time = np.sum([time for i in coord_data.xs])
        xyz_scan_time = xyz.check_scan_time([(x,y,z,l) for x,y,z,l in zip(coord_data.xs, coord_data.ys, coord_data.zs, coord_data.labels)])
        total_scan_time = camera_scan_time + xyz_scan_time
        total_scan_time /= 60
        
        print(total_scan_time, length)
        print(total_scan_time + (total_scan_time*0.05))
        if total_scan_time + (total_scan_time*0.05) >= length:
            print('Timepoint interval too short...')
            return trigger, False, False, True

        # Set user-specified acquisition resolution
        camera_settings.set('sensor_mode', resolution)
        sensor_mode = sensor_modes[camera_settings.get('sensor_mode')]

        width, height = sensor_mode['size']

        featureDict = {
            'camera_settings': {
                'exposure': camera_settings.get('exposure'), # Convert back to exposure units on pi
                'framerate': camera_settings.get('framerate'),
                'width': width,
                'height': height,
                'sensor_mode_ind': resolution,
                'analogue_gain': analogue_gain
            },
            'positions': {
                'x_coordinates': coord_data.xs,
                'y_coordinates': coord_data.ys,
                'z_coordinates': coord_data.zs,
                'labels': coord_data.labels
            },
            'experiment_settings': {
                'timepoints': timepoints,
                'interval': length,
                'capture_length': time,
                'output_path': user_path
            }
        }

        filename = os.path.join(user_path, 'metadata.json')
        with open(filename, 'w') as fp:
            json.dump(featureDict, fp, indent=4)

        acquisition.acquire(
            folder=user_path, positions=acq_num, timepoints=timepoints, interval=length, capture_length=time, # Acquisition parameters
            camera=picam2, exposure=camera_settings.get('exposure'), fps=camera_settings.get('framerate'), sensor_mode=camera_settings.get('sensor_mode'), analogue_gain=camera_settings.get('analogue_gain'), # Camera settings
            stage=stage, leds=leds, light_auto_dim=light_auto_dim, # Hardware instances and settings
            exp_log=experimental_log, # Ancillary instances
            xyz_coords=coord_data, # XYZ coordinates
            email=email # Emails
        ) 

        return trigger, False, False, False


@app.callback(
    output=Output('cancel_state', 'children'),
    inputs=[Input('cancel-acquire-button', 'n_clicks')],
)
def cancel_acquisition(n_clicks):
    if n_clicks is not None:
        acquisition.stop()
    return trigger

@app.callback(
    output=[
        Output('acquire-button', 'disabled'),
        Output('acquire-button', 'children'),
        Output('cancel-acquire-button', 'disabled'),
        Output('acquisition_progress_interval', 'disabled'),

        # Disable or enable UI components depending on acquisition state
        Output('home-xy-button', 'disabled'),
        Output('test-frame-button', 'disabled'),
        Output('camera-live-stream', 'disabled'),
        Output('update-camera-settings', 'disabled'),
        Output('hardware-brightness', 'disabled'),
        Output('load-config-button', 'disabled'),
    ],
    inputs=[
        Input('acquisition_state', 'children'),
        Input('cancel_state', 'children'),
        Input('acquisition_progress_state', 'children')
    ],
)
def acquisition_state_monitor(acquisition_state, cancel_state, acquisition_progress_state):
    if not acquisition.acquiring:
        return [False, 'Start Acquisition', True, True, *[False for i in range(6)]]
    else:
        return [True,  [dbc.Spinner(size='sm'), ' Acquiring...'], False, False, *[True for i in range(6)]]


@app.callback(
    output=[
        Output("timepoint-pg", "value"),
        Output("timepoint-pg", "label"),
        Output("timepoint-pg", "max"),

        Output("embryo-pg", "value"),
        Output("embryo-pg", "label"),
        Output("embryo-pg", "max"),
        
        Output('acquisition_progress_state', 'children'),
    ],
    inputs=[Input('acquisition_progress_interval', 'n_intervals')],
    state=[
        State('total-time-points', 'value'),
        State('acquisition-number', 'value')
    ]
)
def acquisition_progress(n_intervals, timepoints, acq_num):
    labels = coord_data.labels
    current_pos = experimental_log.current
    timepoint, position = current_pos['timepoint'], current_pos['replicate']

    if timepoint is None and position is None:
        return [dash.no_update for i in range(7)]

    timepoint_pg_args = (timepoint+1, f'{timepoint+1}', timepoints)
    if acq_num == 'Single':
        embryo_pg_args = (0, '', 1)
    else:
        embryo_pg_args = (labels.index(position)+1, position, len(labels))

    return [*timepoint_pg_args, *embryo_pg_args, trigger]


# =============================================================================================== #
# -------------------------------------- XYZ stage callbacks ------------------------------------ #
# =============================================================================================== #

@app.long_callback(
    output=Output('xyz-homing-callback', 'children'),
    inputs=[Input('home-xy-button', 'n_clicks')],
    manager=long_callback_manager,
    running=[
        (Output('home-xy-button', 'children'), [dbc.Spinner(size='sm'), ' Homing...'], 'Set Origin'),
        (Output('left-diag-xy-up', 'disabled'), True, False),
        (Output('up-xy', 'disabled'), True, False),
        (Output('right-diag-xy-up', 'disabled'), True, False),
        (Output('left-xy', 'disabled'), True, False),
        (Output('right-xy', 'disabled'), True, False),
        (Output('left-diag-xy-down', 'disabled'), True, False),
        (Output('down-xy', 'disabled'), True, False),
        (Output('right-diag-xy-down', 'disabled'), True, False),
        (Output('up-z', 'disabled'), True, False),
        (Output('down-z', 'disabled'), True, False),
        (Output('grab-xy', 'disabled'), True, False),
        (Output('replace-xy-button', 'disabled'), True, False),
    ],
    prevent_initial_call=True
)
def home_xy_stage(n_clicks):
    if n_clicks:
        stage.setOrigin()
        time.sleep(2)
        return trigger
    else:
        return dash.no_update

@app.callback(
    output=Output('xyz-homing-set-origin', 'children'),
    inputs=[Input('xyz-homing-callback', 'children')],
    prevent_initial_call=True)
def update_relative_xyz(children):
    x,y,z = stage.grabXY()
    relative.start(x=x, y=y, z=z)
    return trigger

# XY movements -----------------------------------------------------------
class Nclick:
    def __init__(self):
        self.n_clicks = 0

mag_fval_map = {0.01: 10, 0.1: 100, 1: 500, 10: 1000}

ldu_xy_clicks = Nclick()
@app.callback(
    output=Output('left-diag-xy-up-div', 'children'),
    inputs=[Input('left-diag-xy-up', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')]
)
def left_diag_up_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > ldu_xy_clicks.n_clicks:
            relative.update(x=-mag, y=-mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F{mag_fval_map[mag]}\n'))
            ldu_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

up_xy_clicks = Nclick()
@app.callback(
    output=Output('up-xy-div', 'children'),
    inputs=[Input('up-xy', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def up_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > up_xy_clicks.n_clicks:
            relative.update(y=-mag)
            stage.xyz.write(str.encode(f'G0 Y{relative.y}F{mag_fval_map[mag]}\n'))
            up_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

rdu_xy_clicks = Nclick()
@app.callback(
    output=Output('right-diag-xy-up-div', 'children'),
    inputs=[Input('right-diag-xy-up', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def right_diag_up_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > rdu_xy_clicks.n_clicks:
            relative.update(x=mag, y=-mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F{mag_fval_map[mag]}\n'))
            rdu_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

left_xy_clicks = Nclick()
@app.callback(
    output=Output('left-xy-div', 'children'),
    inputs=[Input('left-xy', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def left_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > left_xy_clicks.n_clicks:
            relative.update(x=-mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}F{mag_fval_map[mag]}\n'))
            left_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

right_xy_clicks = Nclick()
@app.callback(
    output=Output('right-xy-div', 'children'),
    inputs=[Input('right-xy', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def right_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > right_xy_clicks.n_clicks:
            relative.update(x=mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}F{mag_fval_map[mag]}\n'))
            right_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

ldd_xy_clicks = Nclick()
@app.callback(
    output=Output('left-diag-xy-down-div', 'children'),
    inputs=[Input('left-diag-xy-down', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def left_diag_down_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > ldd_xy_clicks.n_clicks:
            relative.update(x=-mag, y=mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F{mag_fval_map[mag]}\n'))
            ldd_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

down_xy_clicks = Nclick()
@app.callback(
    output=Output('down-xy-div', 'children'),
    inputs=[Input('down-xy', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def down_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > down_xy_clicks.n_clicks:
            relative.update(y=mag)
            stage.xyz.write(str.encode(f'G0 Y{relative.y}F{mag_fval_map[mag]}\n'))
            down_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

rdd_xy_clicks = Nclick()
@app.callback(
    output=Output('right-diag-xy-down-div', 'children'),
    inputs=[Input('right-diag-xy-down', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def right_diag_down_xy(n_clicks, mag):
    if n_clicks:
        if n_clicks > rdd_xy_clicks.n_clicks:
            relative.update(x=mag, y=mag)
            stage.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F{mag_fval_map[mag]}\n'))
            rdd_xy_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

# Z axis ------------------
up_z_clicks = Nclick()
@app.callback(
    output=Output('up-z-div', 'children'),
    inputs=[Input('up-z', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def up_z(n_clicks, mag):
    if n_clicks:
        if n_clicks > up_z_clicks.n_clicks:
            relative.update(z=mag)
            stage.xyz.write(str.encode(f'G0 Z{relative.z}F{mag_fval_map[mag]}\n'))
            up_z_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

down_z_clicks = Nclick()
@app.callback(
    output=Output('down-z-div', 'children'),
    inputs=[Input('down-z', 'n_clicks')],
    state=[State('xyz-magnitude', 'value')])
def down_z(n_clicks, mag):
    if n_clicks:
        if n_clicks > down_z_clicks.n_clicks:
            relative.update(z=-mag)
            stage.xyz.write(str.encode(f'G0 Z{relative.z}F{mag_fval_map[mag]}\n'))
            down_z_clicks.n_clicks += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update
# --------------------------------------------------------

@app.callback(
    output=Output('grab-xy-callback', 'children'),
    inputs=[Input('grab-xy', 'n_clicks')],
    state=[State('xy_coords', 'data')]
)
def grab_xy(n_clicks, data):
    if n_clicks:
        coords = stage.grabXY()

        if coords:
            x,y,z = coords

            if data is not None:
                rows = len(data)
                row_id = rows + 1
            else:
                data = []
                row_id = 0

            #if x in coord_data.xs and y in coord_data.ys and z in coord_data.zs:
            #    return dbc.Alert('Position already exists in table below.', color='danger', dismissable=True)
            #else:
            label=f'Pos{row_id}'
            coord_data.xs.append(x)
            coord_data.ys.append(y)
            coord_data.zs.append(z)
            coord_data.labels.append(label)
            
            coord_data.set_current(x,y,z,label)

            return trigger
        else:
            trigger
    else:
        return trigger


class ReplaceNClicks:
    count = 0

@app.callback(
    output=Output('replace-xy-callback', 'children'),
    inputs=[Input('replace-xy-button', 'n_clicks')],
    state=[
        State('xy_coords', 'selected_rows'),
        State('xy_coords', 'data')
    ])
def replace_xy_in_list(n_clicks, selected_rows, data):
    if n_clicks:
        if n_clicks > ReplaceNClicks.count:
            coords = stage.grabXY()

            if coords:
                x,y,z = coords

                row_coords = data[selected_rows[0]]
                row_coords['x'] = x
                row_coords['y'] = y
                row_coords['z'] = z

                data[selected_rows[0]] = row_coords

                xs = []
                ys = []
                zs = []
                labels = []
                for c in data:
                    xs.append(c['x'])
                    ys.append(c['y'])
                    zs.append(c['z'])
                    labels.append(c['label'])

                coord_data.xs = xs
                coord_data.ys = ys
                coord_data.zs = zs
                coord_data.labels = labels

            ReplaceNClicks.count += 1
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

@app.callback(
    output=[
        Output('generate-xy-button', 'disabled'),
        Output('plate-size', 'disabled')],
    inputs=[
        Input('xy_coords', 'data'),
        Input('cancel-acquire-button', 'disabled')]
    )
def enable_generate_xy(xy, acq_running):
    if not acq_running:
        return True, True
    else:
        if xy is not None:
            a1 = False
            for i,pos in enumerate(xy):
                if 'A1' in pos['label'] or 'a1' in pos['label']:
                    a1 = True

            if a1:
                return False, False
            else:
                return True, True
        else:
            return True, True

# Pre-defined plate sizes
plate_wells = {24:(6,4), 48:(8,6), 96:(12,8), 384:(24,16)}
@app.callback(
    output=Output('generate-xy-callback', 'children'),
    inputs=[Input('generate-xy-button', 'n_clicks')],
    state=[State('xy_coords', 'data'),
           State('plate-size', 'value')])
def generate_xy(n_clicks, data, size):
    if n_clicks:
        a1 = False
        a1_index = None
        for i,pos in enumerate(data):
            if 'A1' in pos['label']:
                a1 = True
                a1_index = i

        if a1:
            xy1 = [
                float(data[a1_index]['x']), 
                float(data[a1_index]['y']), 
                float(data[a1_index]['z']),
                data[a1_index]['label']
            ]

            x,y,z,labels = zip(*xyz.gen_xy_old(xy1, *plate_wells[size]))
            coord_data.xs = x
            coord_data.ys = y
            coord_data.zs = z
            coord_data.labels = labels

            return trigger
        else: 
            return 'Please set first position (A1).'


class RemoveNClicks:
    count = 0

@app.callback(
    output=Output('remove-xy-callback', 'children'),
    inputs=[Input('remove-xy-button', 'n_clicks')],
    state=[
        State('xy_coords', 'selected_rows'),
        State('xy_coords', 'data')]
)
def remove_xy_list(n_clicks, selected_rows, session_data):
    if n_clicks:
        print('Clicked remove')
        if n_clicks > RemoveNClicks.count:
            print('Registered remove click ok')
            if session_data is not None:
                if len(session_data):
                    print('Session data exists for remove')
                    print(session_data)
                    
                    row_coords = session_data[selected_rows[0]]
                    x_,y_,z_,l_ = row_coords.values()
                    
                    xs = []
                    ys = []
                    zs = []
                    labels = []
                    for c in session_data:
                        x,y,z,l = c.values()
                        
                        if x == x_ and y == y_ and z == z_ and l == l_:
                            continue
                                                   
                        xs.append(x)
                        ys.append(y)
                        zs.append(z)
                        labels.append(l)

                    coord_data.xs = xs
                    coord_data.ys = ys
                    coord_data.zs = zs
                    coord_data.labels = labels
                    
                    RemoveNClicks.count += 1

                    return trigger
    else:
        return dash.no_update


@app.callback(
    output=Output('xy_coords', 'data'),
    inputs=[
        Input('loaded-data-callback', 'children'),
        Input('generate-xy-callback', 'children'),
        Input('replace-xy-callback', 'children'),
        Input('remove-xy-callback', 'children'),
        Input('grab-xy-callback', 'children')]
)
def update_xy_list(load, generate, replace, remove, grab):
    print(ctx.triggered_id)

    data = [dict(x=x,y=y,z=z,label=l) for x,y,z,l in zip(coord_data.xs, coord_data.ys, coord_data.zs, coord_data.labels)]
    print(data)
    return data


# Pre-defined marker sizes
marker_sizes = {24:75, 48:55, 96:35, 384:15}
@app.callback(
    output=Output('coord-graph-div', 'children'),
    inputs=[
        Input('xy_coords', 'data'),
        Input('dimensions-switch', 'value')
    ])
def update_graph(data, dim_switch):
    if data:
        first = next(iter(data))
        names = [*first]

        x = [d['x'] for d in data]
        y = [d['y'] for d in data]
        z = [d['z'] for d in data]

        if len(names) < 3:
            if dim_switch:
                fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='markers', marker_size=5)])
            else:
                fig = go.Figure(data=[go.Scatter(x=x, y=y, mode='markers')])
        else:
            labels = [d['label'] for d in data]    
            if dim_switch:
                fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, text=labels, mode='markers', marker_size=5)])
            else:
                fig = go.Figure(data=[go.Scatter(x=x, y=y, text=labels, mode='markers')])

    else:
        if dim_switch:
            fig = go.Figure(data=[go.Scatter3d(x=[], y=[], z=[], mode='markers', marker_size=5)])
        else:
            fig = go.Figure(data=[go.Scatter(x=[], y=[], mode='markers')])

    # Reverse y-axis to correspond with stage origin
    fig.update_layout(
        yaxis = dict(autorange="reversed")
    )
    
    # Enable clicking
    fig['layout']['clickmode'] = 'event+select'

    return html.Div(children=[
        html.Br(),
        renderers.graph(
            ID='xy-pos-graph', 
            fig=fig,
            resolution=(660,420)) # for correct aspect ratio
        ])


@app.callback(
    output=Output('graph-xy-move', 'children'),
    inputs=[
        Input('activate-graph-switch', 'on'),
        Input('xy-pos-graph', 'selectedData')
    ])
def move_by_graph(switch, selectedData):
    if switch:
        if selectedData:
            pointInfo = selectedData['points'][0]
            x,y = (pointInfo['x'], pointInfo['y'])
            print('Clicked:', x,y)

            label = None
            z = None
            try:
                z = pointInfo['z']
            except KeyError:
                z = coord_data.zs[coord_data.index(x,y,z,label)]
            except:
                raise

            if pointInfo['text']: 
                label = pointInfo['text']
            else:
                label = ' '

            prev_coords = coord_data.get_current()
            px,py,pz,pl = prev_coords

            if (px == x) and (py == y) and (pz == z) and (pl == label):
                return dash.no_update
            else:
                relative.start(x=x, y=y, z=z)
                coord_data.set_current(x,y,z,label)
                stage.moveXY(x,y,z)
                
                return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

# =============================================================================================== #
import sys

def teardown():
    """Teardown helper for shutting down various class instances."""
    picam2.close()
    if stage:
        stage.close()
    if leds:
        leds.close()

@app.callback(
    output=Output('close-app-div', 'children'),
    inputs=[Input('close-app', 'n_clicks')])
def shutdown_app(n_clicks):
    if n_clicks:
        teardown()
        print('Shutting down...')
        sys.exit()
    else:
        return dash.no_update

if __name__ == '__main__':
    with open('./app_config.json', 'r') as conf:
        app_conf = json.load(conf)
        local_stream = app_conf['local_camera_stream']

    if not os.path.exists('./snap_images'):
        os.mkdir('./snap_images')

    try:
        if local_stream == 'True':
            from threading import Timer
            import os

            def open_browser():
                os.system('chromium-browser http://127.0.0.1:8050/')

            Timer(2, open_browser).start()
            app.run_server(debug=False)
        else:
            app.run_server(host='0.0.0.0', debug=False)
    finally:
        teardown()

