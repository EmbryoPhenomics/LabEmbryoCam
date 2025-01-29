#!/usr/bin/python

# System wide imports
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import cv2
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
from camera import Camera
import renderers
import emails
import leds
import xyz

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

    manual_control_port = None
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
                manual_control_port = p

        queue.close()

    print(manual_control_port, xyz_port)
    return manual_control_port, xyz_port

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

def gen(camera):
    while True:
        if camera_state.trigger:
            if camera_state.state == 'streaming':
                # Deprecated functionality ----------------------
                # # Reduce resolution for streaming
                # width, height = camera.get('width'), camera.get('height')
                # print(width, height)
                # if width / height == 1:
                #     camera.set('width', 512)
                #     camera.set('height', 512)
                # else:
                #     camera.set('width', 640)
                #     camera.set('height', 480)

                # width, height = camera.get('width'), camera.get('height')
                # print(width, height)
                # -----------------------------------------------

                with camera.platform.start_capture_stream() as cap_gen:
                    for frame in cap_gen:
                        if camera_state.trigger:
                            frame = resize_with_pad(frame, (640, 480))
                            frame = camera.platform.frame_to_bytes(frame)
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                        else:
                            break

            elif camera_state.state == 'snapshot':
                frame = camera.grab()
                print(frame.shape)
                frame = camera.platform.frame_to_bytes(frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                camera_state.trigger = False
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
        self.contrast = None
        self.width = None
        self.height = None
        self.framerate = None

class ExperimentJobLog:
    # To resume acquisitions that have been stopped during acquisition.
    def __init__(self):
        self.log = {}

    def startup(self, replicates, timepoints):
        for r in replicates:
            self.log[r] = dict(
                timepoint=[t for t in list(range(timepoints))],
                acq_time=[None for i in range(timepoints)]
            )

    def update(self, replicate, timepoint, dt):
        self.log[replicate]['acq_time'][timepoint] = dt

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
    def __init__(self):
        self.x = None
        self.y = None
        self.z = None

        # Limits
        self.x1, self.x2 = (22, 210)
        self.y1, self.y2 = (0, 80)
        self.z1, self.z2 = (0, 10)

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

relative = RelativeXYZ()

resolution_presets = {
    384: (512, 384),
    640: (640, 480),
    768: (1024, 768),
    1280:(1280, 720), 
    1920: (1920, 1080),
    256: (256, 256),
    512: (512, 512),
    1024: (1024, 1024),
    2048: (2048, 2048)
}

manual_control_port, xyz_port = check_devices()
# manual_control_port, xyz_port = '/dev/ttyACM0', '/dev/ttyACM1'

# Initiate serial connections
manual_control_serial = serial.Serial(manual_control_port, 115200)
xyz_serial = serial.Serial(xyz_port, 115200)

camera_state = CameraState()
experimental_log = ExperimentJobLog()
hardware = xyz.StageHardware(xyz_serial, None)
coord_data = xyz.Coordinates()
leds = leds.HardwareBrightness(manual_control_serial)
camera = Camera(benchmark=True)
loaded_camera_settings = CameraConfigLoad() 
acquisition_state = AcquisitionState()
user_input_store = UserInputStore()

server = Flask(__name__)
app = dash.Dash(__name__, server=server, long_callback_manager=long_callback_manager, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/app.css', dbc.icons.FONT_AWESOME])
app.config['suppress_callback_exceptions'] = True 
app.layout = layout.app_layout()
# app.css.append_css({'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'})

# For callbacks where no return is needed
trigger = ''

# =============================================================================================== #
# ------------------------------------ Acquire tab callbacks ------------------------------------ #
# =============================================================================================== #

with open('./app_config.json', 'r') as conf:
    app_conf = json.load(conf)
    cam_type = app_conf['camera_platform']
    emails_on = app_conf['emails']

email = emails.Emails()
if emails_on == 'on':
    email.login(app_conf['email_username'], app_conf['email_password'])
    timelib.sleep(1)
email.close()

camera.startup(cam_type)

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
        exposure = camera.get('exposure') / 1000 # For ms on pi
    else:
        exposure = loaded_camera_settings.exposure / 1000 # For ms on pi
    return exposure

@app.callback(
    output=[
        Output('resolution-preset', 'value'),
        Output('resolution-preset', 'disabled')
    ],
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_resolution_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        width = camera.get('width')
        height = camera.get('height')

        return width, False
    else:
        width, height = loaded_camera_settings.width, loaded_camera_settings.height
        return width, False

@app.callback(
    output=Output('fps', 'value'),
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_fps_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        fps = camera.get('framerate')
    else:
        fps = loaded_camera_settings.framerate
    return fps  


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
        State('fps', 'value')
    ])
def update_camera_settings(n_clicks, cam_init, exposure, resolution, fps):
    if n_clicks:
        if camera.platform:
            print(resolution)
            width, height = resolution_presets[resolution]

            camera.set('exposure', exposure * 1000) # Convert back to exposure units on pi
            camera.set('width', width)
            camera.set('height', height)
            camera.set('framerate', fps)
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

@server.route('/video_feed')
def video_feed():
    return Response(gen(camera),
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
        elif camera.platform.is_streaming:
            camera.platform.key = 27 # stop stream by simulating key press
            return trigger, trigger, None
        else:
            # Desktop ----
            if mode:
                TabState.state = 'stream-tab'
                camera.stream(separate_thread=True)
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
        elif camera.platform.is_streaming:
            camera.platform.key = 27 # stop stream by simulating key press
            time.sleep(0.5)

        frame = camera.grab()

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
    output=Output('acquire-path-input', 'value'),
    inputs=[Input('path-select', 'n_clicks')]
)
def get_acq_path(n_clicks):
    if n_clicks:
        root = Tk()
        folder_selected = tkfilebrowser.askopendirname(parent=root)
        root.destroy()
        return folder_selected
    else:
        return dash.no_update

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
    inputs=[Input('load-config-button', 'filename')])
def upload_config(filename):
    if filename == None:
        return dash.no_update
    else:
        filename = './configs/' + filename

        with open(filename, 'r') as fp:
            data = json.load(fp)

            loaded_camera_settings.exposure = data['camera_settings']['exposure']
            loaded_camera_settings.framerate = data['camera_settings']['framerate']
            loaded_camera_settings.width = data['camera_settings']['width']
            loaded_camera_settings.height = data['camera_settings']['height']

            coord_data.xs = data['positions']['x_coordinates']
            coord_data.ys = data['positions']['y_coordinates']
            coord_data.zs = data['positions']['z_coordinates']
            coord_data.labels = data['positions']['labels']

        return trigger

@app.callback(
    output=Output('config-save-callback', 'children'),
    inputs=[Input('save-config-button', 'n_clicks')],
    state=[
        State('config-name-input', 'value'),
        State('exposure', 'value'),
        State('fps', 'value'),     
        State('resolution-preset', 'value'),
        State('total-time-points', 'value'),
        State('acq-length', 'value'),
        State('each-time-limit', 'value'),
        State('acquire-path-input', 'value'),
    ])
def save_config(n_clicks, config_name, exposure, fps, resolution, timepoints, interval, length, path):
    if n_clicks is None:
        return dash.no_update
    else:
        width, height = resolution_presets[resolution]

        featureDict = {
            'camera_settings': {
                'exposure': exposure * 1000, # Convert back to exposure units on pi
                'framerate': fps,
                'width': width,
                'height': height
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

        filename = f'./configs/{config_name}.json'

        with open(filename, 'w') as fp:
            json.dump(featureDict, fp, indent=4)

# ============================================================= #
# ------------------ Acquisitions callbacks ------------------- #
# ============================================================= #

def to_list(vals):
    if not isinstance(vals, list):
        if isinstance(vals, float or int or str):
            vals = [vals]
        else:
            vals = list(vals)
    return vals

def pack_results(data):
    t_,c,a,i,tp,e,mft,lft,hft = map(to_list, data)
    d = dict(TotalTime=t_, AcquisitionTime=c, AncillaryTime=a, 
             IncompleteFrames=i, MeanFrameTime=mft, MinFrameTime=lft, MaxFrameTime=hft,
             Timepoint=tp, Embryo=e)
    df = pd.DataFrame(data=d)   
    return df

def send_email(email_cls, timepoint, data, paths, checklist):
    email = emails.Emails()
    email.login(email_cls.username, email_cls.password)

    # Pause the email system until all videos have finished being captured.
    while True:
        out = checklist.get()
        if out:
            break

    try:
        if email.isLoggedIn:
            outfiles = [] 

            if isinstance(paths, list):
                for file in paths:
                    video = cv2.VideoCapture(file)
                    _, frame = video.read()
                    new_file = re.sub('.avi', '.png', file)
                    cv2.imwrite(new_file, frame)
                    video.release()

                    outfiles.append(new_file)
            else:
                video = cv2.VideoCapture(paths)
                _, frame = video.read()
                new_file = re.sub('.avi', '.png', paths)
                cv2.imwrite(new_file, frame)
                video.release()

                outfiles.append(new_file)

            text = f"""\
            LabEP update: Timepoint {timepoint}

            No. of embryos imaged: {len(paths)}

            See attached files for still images of embryos at this timepoint."""

            email.send(f'LabEP update: timepoint {timepoint}', text, outfiles)

            for file in outfiles:
                os.remove(file)
    finally:
        email.close()

def convert_to_avi(files, fps, checklist, codec='MJPG', delete_npy=True):
    # For converting numpy files to avi's for ease of use
    for file in files:
        array = np.load(file)
        h, w, c = array.shape[1:]
        writer = cv2.VideoWriter(re.sub('.npy', '.avi', file), cv2.VideoWriter_fourcc(*codec), fps, (w,h))
        for frame in array:
            writer.write(frame)

        writer.release()
        if delete_npy:
            os.remove(file)
        
    checklist.put(True)


def post_acq_gui(positions, timepoint, files, checklist, terminate_queue):
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.5
    fontColor = (255,255,255)
    lineType = 1

    # Pause the gui creator until all videos have finished being converted
    while True:
        out = checklist.get()
        
        if not terminate_queue.empty():
            terminate = terminate_queue.get()
            
            if terminate:
                print('[INFO]: Not enough time between acquisitions to display GUI.')
                return
        if out:
            break

    position_frames = []
    for p, f in zip(positions, files):
        video = cv2.VideoCapture(f)
        s, frame = video.read()
        cv2.putText(
            frame, f'Position: {p}',
            tuple(map(int, (0.01*frame.shape[1], 0.92*frame.shape[0]))),
            font, fontScale, fontColor, lineType)

        cv2.putText(
            frame, f'Timepoint: {timepoint}',
            tuple(map(int, (0.01*frame.shape[1], 0.96*frame.shape[0]))),
            font, fontScale, fontColor, lineType)

        position_frames.append(frame)
        video.release()
    
    if not terminate_queue.empty():
        terminate = terminate_queue.get()
        
        if terminate:
            print('[INFO]: Not enough time between acquisitions to display GUI.')
            return

    fig, ax = plt.subplots()
    im = ax.imshow(position_frames[0], cmap='gray')
    fig.subplots_adjust(bottom=0.25)

    axpos = fig.add_axes([0.25, 0.1, 0.65, 0.03])
    pos_slider = Slider(
        ax=axpos,
        label='Position',
        valmin=1,
        valmax=len(position_frames),
        valinit=1,
        valstep=1,
    )

    # The function to be called anytime a slider's value changes
    def update(val):
        im.set_array(position_frames[val])
        fig.canvas.draw_idle()

    pos_slider.on_changed(update)

    plt.show()

    # gui = vuba.FramesGUI(position_frames, title='Position Viewer:')

    # @gui.method
    # def main(gui):
    #     frame = gui.frame.copy()
    #     return frame

    # def close_without_key():
    #     # Execute first method to launch the gui
    #     firstfunc = gui.trackbars[[*gui.trackbars][0]]
    #     func = firstfunc.method
    #     min = firstfunc.min
    #     func(min)

    #     while True:
    #        cv2.pollKey()
           
    #        if not terminate_queue.empty():
    #            terminate = terminate_queue.get()
               
    #            if terminate:
    #                cv2.destroyAllWindows()
    #                break
            
    # gui.run = close_without_key
    # gui.run()

# Amount of units of moved per second for xy stage
units_per_sec = 6
@app.long_callback(
    output=[
        Output('hiddenAcquire', 'children'),
        Output('acquisition-live-stream-popup', 'is_open'),
        Output('acquisition-folder-popup', 'is_open')],
    inputs=[Input('acquire-button', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('total-time-points', 'value'),
        State('acq-length', 'value'),
        State('each-time-limit', 'value'),
        State('exposure', 'value'),
        State('fps', 'value'),     
        State('resolution-preset', 'value'),
        State('acquire-path-input', 'value'),
        State('xy_coords', 'data'),
        State('acquisition-number', 'value'),
        State('light-auto-dimming', 'value')
    ],
    manager=long_callback_manager,
    running=[
        (Output('acquire-button', 'children'), [dbc.Spinner(size='sm'), ' Acquiring...'], 'Start acquisition'),
        (Output('acquire-button', 'disabled'), True, False),
        (Output('cancel-acquire-button', 'disabled'), False, True),
        (Output('home-xy-button', 'disabled'), True, False),
        (Output('test-frame-button', 'disabled'), True, False),
        (Output('camera-live-stream', 'disabled'), True, False),
        (Output('update-camera-settings', 'disabled'), True, False),
        (Output('hardware-brightness', 'disabled'), True, False),
        (Output('load-config-button', 'disabled'), True, False),
        # (Output('xy_coords', 'editable'), True, False), # Removed for now because it makes the table uneditable despite arguments being correct.
    ],
    cancel=[Input('cancel-acquire-button', 'n_clicks')],
    progress=[
        Output("timepoint-pg", "value"), Output("timepoint-pg", "label"), Output("timepoint-pg", "max"), 
        Output("embryo-pg", "value"), Output("embryo-pg", "label"), Output("embryo-pg", "max"), 
    ]
)
def acquire(set_progress, n_clicks, cam_init, timepoints, length, time, exposure, fps, resolution, user_path, xy_data, acq_num, light_auto_dim):
    if n_clicks is None:
        return dash.no_update, False, False
    else:
        acquisition_state.started()

        if camera_state.trigger and camera_state.state == 'streaming':
            print('Streaming currently, will fail...')
            acquisition_state.finished()
            return trigger, True, False

        experimental_log.clear()

        # Create parent folder
        DATA_FOLDER = user_path
        print(DATA_FOLDER)

        # Set user-specified acquisition resolution
        width, height = resolution_presets[resolution]
        camera.set('width', width)
        camera.set('height', height)

        if len(os.listdir(DATA_FOLDER)):
            return trigger, False, True

        width, height = resolution_presets[resolution]

        featureDict = {
            'camera_settings': {
                'exposure': exposure * 1000, # Convert back to exposure units on pi
                'framerate': fps,
                'width': width,
                'height': height
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

        if acq_num == 'Single': 
            print('Starting acquisition...')          
            if length == 0:
                # Acquire footage
                path = os.path.join(DATA_FOLDER, 'continuous.avi')
                camera.acquire(path, round(timepoints*time), in_memory=False)
                ((total, capture, ancillary), (complete, incomplete), ft) = camera.acq_data
                time_data = [(total, capture, ancillary, incomplete, 
                                 1, 0, ft.mean(), ft.min(), ft.max()),]

                # Progress bar info
                set_progress((0, '', 1, 0, '', 1))

            else:  

                # Grab current led value to change to during acquisition and switch off after each timepoint
                LED_VALUE = leds.current
                if not light_auto_dim:
                    leds.set(0)

                timelib.sleep(1)

                experimental_log.startup(['A'], timepoints)
                time_data = []
                paths = []
                for t in range(timepoints):
                    print(f'Acquiring footage for timepoint {t+1}...')

                    # Turn leds on
                    leds.set(LED_VALUE)
                    timelib.sleep(1)

                    path = os.path.join(DATA_FOLDER, f'timepoint{t+1}.npy')
                    paths.append(path)

                    # Acquire footage
                    t1 = timelib.time()
                    camera.acquire(path, time, in_memory=True)
                    timelib.sleep(2) # session pause to not cause a session hang
                    ((total, capture, ancillary), (complete, incomplete), ft) = camera.acq_data
                    timepointData = (total, capture, ancillary, incomplete, 
                                    str(t), 0, ft.mean(), ft.min(), ft.max())
                    time_data.append(timepointData)
                    t2 = timelib.time()

                    # Progress bar info
                    set_progress((t+1, f'{t+1}', timepoints, 0, '', 1))
                    experimental_log.update('A', t, str(datetime.datetime.fromtimestamp(t2)))

                    converted_checklist = mp.Queue()
                    convert_proc = mp.Process(target=convert_to_avi, args=([path], fps, converted_checklist))
                    convert_proc.start()

                    path = re.sub('.npy', '.avi', path) # for emails
                    # Send progress updates
                    if email.isLoggedIn:
                        email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*[timepointData, ]), path, converted_checklist))
                        email_proc.start()

                    # Turn leds off
                    if not light_auto_dim:
                        leds.set(0)
                    timelib.sleep(1)

                    acqTime = t2 - t1
                    print(f'Sleep time: {length*60 - acqTime}')

                    timelib.sleep(length*60 - acqTime)  
                    
        elif acq_num == 'Multiple': 
            if length == 0:
                return 'Cannot have no acquisition interval when acquiring footage for multiple positions.', False, False

            # Initial setup
            first = next(iter(xy_data))
            names = [*first]

            if len(names) < 3:
                return 'Coordinate positions must have labels to begin acquisition.', False, False

            labels = [d['label'] for d in xy_data]

            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            if not light_auto_dim:
                leds.set(0)

            timelib.sleep(1)

            # Creation of filepaths
            paths = {}
            for replicate in labels:
                paths[replicate] = []
                replicate_path = os.path.join(DATA_FOLDER, replicate + '/')

                if not os.path.exists(replicate_path):
                    os.makedirs(replicate_path)

                for t in range(timepoints):
                    timepoint_path = os.path.join(replicate_path, f'timepoint{t+1}.npy')
                    paths[replicate].append(timepoint_path)

            experimental_log.startup(labels, timepoints)

            print('Starting acquisition...')
            time_data = []
            for t in range(timepoints):
                print(f'Acquiring footage for timepoint {t+1}...')

                # Turn leds on
                leds.set(LED_VALUE)
                timelib.sleep(1)

                # Set to first well position
                first = next(iter(xy_data))
                prev_x, prev_y, prev_z = hardware.grabXY()
                x,y,z = (first['x'], first['y'], first['z'])
                dist = np.sqrt((x-prev_x)**2 + (y-prev_y)**2 + (z-prev_z)**2)
                hardware.moveXY(x,y,z)
                
#                 if abs(x-prev_x) > 0 and abs(y-prev_y) > 0:
#                     timelib.sleep(dist/(units_per_sec/1.5))
#                 else:
#                     timelib.sleep(dist/units_per_sec)

                t1 = timelib.time()
                timepointPaths = []
                timepointData = []
                for label,pos in zip(labels, xy_data):
                    # Position move
                    prev_x, prev_y = (x, y)
                    x,y,z = (pos['x'], pos['y'], pos['z'])
                    dist = np.sqrt((x-prev_x)**2 + (y-prev_y)**2 + (z-prev_z)**2)
                    hardware.moveXY(x,y,z) # Added wait for 'ok'

#                     if abs(x-prev_x) > 0 and abs(y-prev_y) > 0:
#                         timelib.sleep(dist/(units_per_sec/1.5))
#                     else:
#                         timelib.sleep(dist/units_per_sec)

                    # Acquire footage
                    path = paths[label][t]
                    timepointPaths.append(path)
                    camera.acquire(path, time, in_memory=True)
                    timelib.sleep(0.5) # session pause to not cause a session hang
                    ((total, capture, ancillary), (complete, incomplete), ft) = camera.acq_data
                    timepoint_data = (total, capture, ancillary, incomplete, 
                                    str(t), label, ft.mean(), ft.min(), ft.max())
                    time_data.append(timepoint_data)
                    timepointData.append(timepoint_data)

                    # Progress bar info
                    set_progress((t+1, f'{t+1}', timepoints, labels.index(label)+1, label, len(labels)))
                    experimental_log.update(label, t, datetime.datetime.fromtimestamp(t1))
                    
                converted_checklist = mp.Queue()
                convert_proc = mp.Process(target=convert_to_avi, args=(timepointPaths, fps, converted_checklist))
                convert_proc.start()

                timepointPaths = [re.sub('.npy', '.avi', file) for file in timepointPaths] # For emails below

                terminate_queue = mp.Queue()
                #gui_proc = mp.Process(target=post_acq_gui, args=(labels, t, timepointPaths, converted_checklist, terminate_queue))
                #gui_proc.start()

                # Send progress updates
                if email.isLoggedIn:
                    email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*timepointData), timepointPaths, converted_checklist))
                    email_proc.start()

                experimental_log.export(os.path.join(DATA_FOLDER, 'time_data.csv'))

                # Turn leds off
                if not light_auto_dim:
                    leds.set(0)

                timelib.sleep(1)

                t2 = timelib.time()
                acqTime = t2 - t1
                print(f'Sleep time: {length*60 - acqTime}')

                timelib.sleep(length*60 - acqTime)
                terminate_queue.put(True)
                timelib.sleep(0.5)
                #gui_proc.terminate()
                timelib.sleep(0.1)

        print('Completed acquisition.')
        df = pack_results(zip(*time_data))
        df.to_csv(os.path.join(DATA_FOLDER, 'capture_data.csv'))

        if email.isLoggedIn:
            text = f"""\
            LabEP update: Completed acquisition.
            """

            email.login(email.username, email.password)
            email.send(f'LabEP update: Completed acquisition.', text, None)
            email.close()

        acquisition_state.finished()

        return trigger, False, False

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
        hardware.setOrigin()
        x,y,z = hardware.grabXY()
        relative.start(x=x, y=y, z=z)
        return trigger
    else:
        return dash.no_update

@app.callback(
    output=Output('xyz-homing-set-origin', 'children'),
    inputs=[Input('xyz-homing-callback', 'children')],
    prevent_initial_call=True)
def update_relative_xyz(children):
    x,y,z = hardware.grabXY()
    relative.start(x=x, y=y, z=z)
    return trigger

# XY movements -----------------------------------------------------------
class Nclick:
    def __init__(self):
        self.n_clicks = 0

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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 X{relative.x}Y{relative.y}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 Z{relative.z}F1000\n'))
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
            hardware.xyz.write(str.encode(f'G0 Z{relative.z}F1000\n'))
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
        coords = hardware.grabXY()

        if coords:
            x,y,z = coords

            if data is not None:
                rows = len(data)
                row_id = rows + 1
            else:
                data = []
                row_id = 0

            if x in coord_data.xs and y in coord_data.ys and z in coord_data.zs:
                return dash.no_update
            else:
                label=f'Pos{row_id}'
                coord_data.xs.append(x)
                coord_data.ys.append(y)
                coord_data.zs.append(z)
                coord_data.labels.append(label)

                return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update


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
            coords = hardware.grabXY()

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
                if 'A1' in pos['label']:
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
                data[a1_index]['x'], 
                data[a1_index]['y'], 
                data[a1_index]['z'],
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

@app.callback(
    output=Output('remove-xy-callback', 'children'),
    inputs=[Input('xy_coords', 'data')]
)
def remove_xy_list(session_data):
    print('Session:')
    print(session_data)
    if session_data is not None:
        if len(session_data):
            session_data = pd.DataFrame(session_data).to_dict(orient='list')

            coord_data.xs = session_data['x']
            coord_data.ys = session_data['y']
            coord_data.zs = session_data['z']
            coord_data.labels = session_data['label']

            return trigger
        else:
            return dash.no_update
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
                hardware.moveXY(x,y,z)
                
                return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

# =============================================================================================== #
import sys

def teardown():
    """Teardown helper for shutting down various class instances."""
    camera.close()
    hardware.close()
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
                os.system('chromium-browser --kiosk http://127.0.0.1:8050/')

            Timer(2, open_browser).start()
            app.run_server(debug=False)
        else:
            app.run_server(host='0.0.0.0', debug=False)
    finally:
        teardown()

