# System wide imports
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import cv2
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
import datetime

## Diskcache
import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# App specific modules
import layout
from camera import Camera
import renderers
import emails
import leds
import xyz
import embryocv

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

def gen(camera):
    while True:
        if camera_state.trigger:
            if camera_state.state == 'streaming':

                # Reduce resolution for streaming
                width, height = camera.get('width'), camera.get('height')
                print(width, height)
                if width / height == 1:
                    camera.set('width', 512)
                    camera.set('height', 512)
                else:
                    camera.set('width', 640)
                    camera.set('width', 480)

                with camera.platform.start_capture_stream() as cap_gen:
                    for frame in cap_gen:
                        if camera_state.trigger:
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

# class UserInputStore:
#     def __init__(self):
        
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

resolution_presets = {
    640: (640, 480), 
    1280:(1280, 720), 
    1920: (1920, 1080),
    256: (256, 256),
    512: (512, 512),
    1024: (1024, 1024),
    2048: (2048, 2048)
}

light_port, joystick_port, xyz_port = check_devices()

camera_state = CameraState()
email = emails.Emails()
experimental_log = ExperimentJobLog()
hardware = xyz.StageHardware(xyz_port, joystick_port)
coord_data = xyz.Coordinates()
leds = leds.HardwareBrightness(light_port)
camera = Camera(benchmark=True)
loaded_camera_settings = CameraConfigLoad() 

# external_stylesheets = ['./assets/app.css']
server = Flask(__name__)
app = dash.Dash(__name__, server=server, long_callback_manager=long_callback_manager, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/app.css'])
app.config['suppress_callback_exceptions'] = True 
app.layout = layout.app_layout()
# app.css.append_css({'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'})

# For callbacks where no return is needed
trigger = '.'

# =============================================================================================== #
# ------------------------------------ Acquire tab callbacks ------------------------------------ #
# =============================================================================================== #

with open('./app_config.json', 'r') as conf:
    app_conf = json.load(conf)
    cam_type = app_conf['camera_platform']

camera.startup(cam_type)

# ============================================================= #
# ------------------ Html rendering callbacks ----------------- #
# ============================================================= #

@app.callback(
    output=Output('brightness-control', 'children'),
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_brightness_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        exposure = camera.get('exposure') / 1000 # For ms on pi
        contrast = camera.get('contrast')
        return renderers.render_brightness_ui(data=dict(exposure=exposure, contrast=contrast))
    else:
        data = dict(
            exposure=loaded_camera_settings.exposure / 1000, # For ms on pi
            contrast=loaded_camera_settings.contrast)
        return renderers.render_brightness_ui(data)

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

        return dict(label=f'{width}x{height}', value=width), False
    else:
        width, height = loaded_camera_settings.width, loaded_camera_settings.height
        return width, False

@app.callback(
    output=Output('fps-control', 'children'),
    inputs=[
        Input('connect-cam-callback', 'children'),
        Input('loaded-data-callback', 'children')
    ])
def update_fps_ui(cam_init, loaded_data):
    if trigger not in [loaded_data]:
        fps = camera.get('framerate')
        return renderers.render_fps_ui(data=dict(framerate=fps))
    else:
        data = dict(framerate=loaded_camera_settings.framerate)
        return renderers.render_fps_ui(data)   


# ============================================================= #
# ------------------ Updating UI callbacks -------------------- #
# ============================================================= #

@app.callback(
    output=Output('hardware-brightness-callback', 'children'),
    inputs=[Input('hardware-brightness', 'value')])
def update_hardware_brightness(value):
    leds.set(value)

@app.callback(
    output=Output('login-callback', 'children'),
    inputs=[Input('email-login', 'n_clicks')],
    state=[
        State('email-username', 'value'),
        State('email-password', 'value')
    ])
def login_email(n_clicks, username, password):
    if n_clicks:
        if username and password:
            try:
                email.login(username, password)
            except Exception as e:
                return e
            finally:
                email.close() # Close so we can start new servers in separate processes 
                               # for acquisitions below
    else:
        return dash.no_update

@app.callback(
    output=Output('hidden-update-callback', 'children'),
    inputs=[Input('update-camera-settings', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('exposure', 'value'),
        State('contrast', 'value'),
        State('resolution-preset', 'value'),
        State('fps', 'value')
    ])
def update_camera_settings(n_clicks, cam_init, exposure, contrast, resolution, fps):
    if n_clicks:
        if camera.platform:
            width, height = resolution_presets[resolution]

            camera.set('exposure', exposure * 1000) # Convert back to exposure units on pi
            camera.set('contrast', contrast)
            camera.set('width', width)
            camera.set('height', height)
            camera.set('framerate', fps)
        else:
            return dash.no_update
    else:
        return dash.no_update



@server.route('/video_feed')
def video_feed():
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.callback(
    output=Output('camera-state-live-view', 'children'),
    inputs=[Input('camera-live-stream', 'n_clicks')],
    state=[State('connect-cam-callback', 'children')]
)
def start_stop_live_view(n_clicks, cam_init):
    if n_clicks is not None:
        camera_state.on_off('streaming')
        return trigger
    else:
        return dash.no_update

@app.callback(
    output=Output('camera-state-snapshot', 'children'),
    inputs=[Input('test-frame-button', 'n_clicks')],
    state=[State('connect-cam-callback', 'children')])
def update_still_image(n_clicks, cam_init):
    if n_clicks is None:
        return dash.no_update
    else:
        camera_state.on_off('snapshot')

@app.callback(
    output=Output('total-wells', 'children'),
    inputs=[Input('xy_coords', 'data')])
def update_well_number(data):
    x = [d['x'] for d in data] # always will be filled
    return len(x)

@app.callback(
    output=Output('acquire-outpath-check', 'children'),
    inputs=[Input('acquire-path-input', 'value')])
def check_acquire_path(path):
    if path:
        if not os.path.isdir(path):
            return 'Specified path is not to a directory.'
        else:
            return ''
    else:
        return ''

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

            loaded_camera_settings.exposure = data['exposure']
            loaded_camera_settings.framerate = data['framerate']
            loaded_camera_settings.contrast = data['contrast']
            loaded_camera_settings.width = data['width']
            loaded_camera_settings.height = data['height']

            coord_data.xs = data['x_coordinates']
            coord_data.ys = data['y_coordinates']
            coord_data.zs = data['z_coordinates']
            coord_data.labels = data['labels']

        return trigger

@app.callback(
    output=Output('config-save-callback', 'children'),
    inputs=[Input('save-config-button', 'n_clicks')],
    state=[
        State('config-name-input', 'value'),
        State('exposure', 'value'),
        State('contrast', 'value'),
        State('fps', 'value'),     
        State('resolution-preset', 'value')
    ])
def save_config(n_clicks, config_name, exposure, contrast, fps, resolution):
    if n_clicks is None:
        return dash.no_update
    else:
        width, height = resolution_presets[resolution]

        featureDict = {
            'exposure': exposure * 1000, # Convert back to exposure units on pi
            'contrast': contrast,
            'framerate': fps,
            'width': width,
            'height': height,
            'x_coordinates': coord_data.xs,
            'y_coordinates': coord_data.ys,
            'z_coordinates': coord_data.zs,
            'labels': coord_data.labels
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

def send_email(email_cls, timepoint, data, paths):
    email = emails.Emails()
    email.login(email_cls.username, email_cls.password)

    # Pause the email system until all videos have finished being captured.
    while True:
        paths_true = []

        for p in paths:
            if os.path.exists(p):
                paths_true.append(True)

        if len(paths_true) == len(paths):
            break

        time.sleep(1)

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
            LabEmbryoCam update: Timepoint {timepoint}:

            No. of embryos imaged: {len(paths)}

            See attached files for still images of embryos at this timepoint."""

            email.send(f'LabEmbryoCam update: timepoint {timepoint}', text, outfiles)

            for file in outfiles:
                os.remove(file)
    finally:
        email.close()

def embryocv_compute(file, outpath=None, verbose=False):
    ''' Convenience function for processing callback below. '''
    lenFrames = embryocv.frameCount(file)
    fps = embryocv.frameRate(file)

    frameStats, blockWiseMeans = embryocv.blockMeans(embryocv.framesFromVideo(file), lenFrames, verbose)
    signalData = embryocv.signalWelch(blockWiseMeans, fps, verbose)

    results, mxLength = embryocv.packResults(frameStats, blockWiseMeans, signalData, verbose)
    
    if outpath is None: outpath = re.sub('.avi', '.h5', file)
    embryocv.exportResults(results, outpath)
    
    return mxLength

def embryocv_compute_process(queue):
    while True:
        if not queue.empty():
            file = queue.get()

            if file == None:
                break

            embryocv_compute(file)

def convert_to_avi(files, fps, codec='MJPG', delete_npy=True):
    # For converting numpy files to avi's for ease of use
    for file in files:
        array = np.load(file)
        h, w = array.shape[1:]
        writer = cv2.VideoWriter(re.sub('.npy', '.avi', file), cv2.VideoWriter_fourcc(*codec), fps, (w,h))
        for frame in array:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            writer.write(frame)

        writer.release()
        if delete_npy:
            os.remove(file)


# Amount of units of moved per second for xy stage
units_per_sec = 6
@app.long_callback(
    output=Output('hiddenAcquire', 'children'),
    inputs=[Input('acquire-button', 'n_clicks')],
    state=[
        State('connect-cam-callback', 'children'),
        State('total-time-points', 'value'),
        State('acq-length', 'value'),
        State('each-time-limit', 'value'),
        State('fps', 'value'),
        State('acquire-path-input', 'value'),
        State('xy_coords', 'data'),
        State('acquisition-number', 'value')
    ],
    manager=long_callback_manager,
    running=[
        (Output('acquire-button', 'disabled'), True, False),
        (Output('cancel-acquire-button', 'disabled'), False, True)
    ],
    cancel=[Input('cancel-acquire-button', 'n_clicks')],
    progress=[
        Output("timepoint-pg", "value"), Output("timepoint-pg", "label"), Output("timepoint-pg", "max"), 
        Output("embryo-pg", "value"), Output("embryo-pg", "label"), Output("embryo-pg", "max"), 
    ],
)
def acquire(set_progress, n_clicks, cam_init, timepoints, length, time, fps, user_path, xy_data, acq_num):
    if n_clicks is None:
        return dash.no_update
    else:
        experimental_log.clear()

        if acq_num == 'Single': 
            print('Starting acquisition...')          
            if length == 0:
                # Acquire footage
                path = os.path.join(user_path, 'continuous.avi')
                camera.acquire(path, round(timepoints*time), in_memory=False)
                ((total, capture, ancillary), (complete, incomplete), ft) = camera.acq_data
                time_data = [(total, capture, ancillary, incomplete, 
                                 1, 0, ft.mean(), ft.min(), ft.max()),]

                # Progress bar info
                set_progress((0, '', 1, 0, '', 1))

            else:  

                # Grab current led value to change to during acquisition and switch off after each timepoint
                LED_VALUE = leds.current
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

                    path = os.path.join(user_path, f'timepoint{t+1}.npy')
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

                    convert_proc = mp.Process(target=convert_to_avi, args=([path], fps))
                    convert_proc.start()

                    path = re.sub('.npy', '.avi', path) # for emails
                    # Send progress updates
                    if email.isLoggedIn:
                        email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*[timepointData, ]), path))
                        email_proc.start()

                    # file_queue.put(path)

                    # Turn leds off
                    leds.set(0)
                    timelib.sleep(1)

                    acqTime = t2 - t1
                    print(f'Sleep time: {length*60 - acqTime}')

                    timelib.sleep(length*60 - acqTime)  
                    
        elif acq_num == 'Multiple': 
            if length == 0:
                return 'Cannot have no acquisition interval when acquiring footage for multiple positions.'

            # Initial setup
            first = next(iter(xy_data))
            names = [*first]

            if len(names) < 3:
                return 'Coordinate positions must have labels to begin acquisition.'

            labels = [d['label'] for d in xy_data]

            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            leds.set(0)
            timelib.sleep(1)

            # Creation of filepaths
            paths = {}
            for replicate in labels:
                paths[replicate] = []
                replicate_path = os.path.join(user_path, replicate + '/')

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
                dist = np.sqrt((x-prev_x)**2 + (y-prev_y)**2)
                hardware.moveXY(x,y,z)
                
                if abs(x-prev_x) > 0 and abs(y-prev_y) > 0:
                    timelib.sleep(dist/(units_per_sec/2))
                else:
                    timelib.sleep(dist/units_per_sec)

                t1 = timelib.time()
                timepointPaths = []
                timepointData = []
                for label,pos in zip(labels, xy_data):
                    # Position move
                    prev_x, prev_y = (x, y)
                    x,y,z = (pos['x'], pos['y'], pos['z'])
                    dist = np.sqrt((x-prev_x)**2 + (y-prev_y)**2)
                    hardware.moveXY(x,y,z) # Added wait for 'ok'

                    if abs(x-prev_x) > 0 and abs(y-prev_y) > 0:
                        timelib.sleep(dist/(units_per_sec/2))
                    else:
                        timelib.sleep(dist/units_per_sec)

                    # Acquire footage
                    path = paths[label][t]
                    timepointPaths.append(path)
                    camera.acquire(path, time, in_memory=True)
                    timelib.sleep(2) # session pause to not cause a session hang
                    ((total, capture, ancillary), (complete, incomplete), ft) = camera.acq_data
                    timepoint_data = (total, capture, ancillary, incomplete, 
                                    str(t), label, ft.mean(), ft.min(), ft.max())
                    time_data.append(timepoint_data)
                    timepointData.append(timepoint_data)

                    # Progress bar info
                    set_progress((t+1, f'{t+1}', timepoints, labels.index(label)+1, label, len(labels)))
                    experimental_log.update(label, t, datetime.datetime.fromtimestamp(t1))

                convert_proc = mp.Process(target=convert_to_avi, args=(timepointPaths, fps))
                convert_proc.start()

                timepointPaths = [re.sub('.npy', '.avi', file) for file in timepointPaths] # For emails below

                # Send progress updates
                if email.isLoggedIn:
                    email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*timepointData), timepointPaths))
                    email_proc.start()

                experimental_log.export(os.path.join(user_path, 'time_data.csv'))

                # Turn leds off
                leds.set(0)
                timelib.sleep(1)

                t2 = timelib.time()
                acqTime = t2 - t1
                print(f'Sleep time: {length*60 - acqTime}')

                timelib.sleep(length*60 - acqTime)
                
        print('Completed acquisition.')
        df = pack_results(zip(*time_data))
        df.to_csv(os.path.join(user_path, 'capture_data.csv'))

# =============================================================================================== #
# -------------------------------------- XYZ stage callbacks ------------------------------------ #
# =============================================================================================== #

@app.callback(
    output=Output('xyz-homing-callback', 'children'),
    inputs=[Input('home-xy-button', 'n_clicks')])
def home_xy_stage(n_clicks):
    if n_clicks:
        hardware.initialiseXYZ()
        hardware.setOrigin()
        timelib.sleep(2) # wait for stage to home properly
        print('Finished xyz stage homing.')
    else:
        return dash.no_update

@app.callback(
    output=Output('manual-controls-callback', 'children'),
    inputs=[Input('manual-controls', 'on')])
def enable_joystick(value):
    if value == True:
        hardware.launchJoystick()
        return dash.no_update
    else:
        hardware.disableJoystick()
        return dash.no_update

@app.callback(
    output=Output('grab-xy-callback', 'children'),
    inputs=[
        Input('grab-xy', 'n_clicks'),
        Input('xy_coords', 'data'),
    ]
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
        Input('xy_coords', 'selected_rows'),
        Input('xy_coords', 'data')
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
    inputs=[Input('xy_coords', 'data')])
def enable_generate_xy(xy):
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
        return False, False

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
                fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='markers')])
            else:
                fig = go.Figure(data=[go.Scatter(x=x, y=y, mode='markers')])
        else:
            if len(x) in [24,48,96,384]:
                marker = dict(size=marker_sizes[len(x)], line=(dict(width=1)))
            else:
                marker = None

            labels = [d['label'] for d in data]    
            if dim_switch:
                fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, text=labels, mode='markers', marker=marker)])
            else:
                fig = go.Figure(data=[go.Scatter(x=x, y=y, text=labels, mode='markers', marker=marker)])

        # Enable clicking
        fig['layout']['clickmode'] = 'event+select'

        return html.Div(children=[
            html.Br(),
            renderers.graph(
                ID='xy-pos-graph', 
                fig=fig,
                resolution=(660,420)) # for correct aspect ratio
            ])
    else:
        return dash.no_update

@app.callback(
    output=Output('graph-xy-move', 'children'),
    inputs=[
        Input('activate-graph-switch', 'on'),
        Input('xy-pos-graph', 'clickData')
    ])
def move_by_graph(switch, clickData):
    if switch:
        if clickData:
            pointInfo = clickData['points'][0]
            x,y = (pointInfo['x'], pointInfo['y'])

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

            coord_data.set_current(x,y,z,label)
            hardware.moveXY(x,y,z)
            return trigger
        else:
            return dash.no_update
    else:
        return dash.no_update

# =============================================================================================== #

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
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        return dash.no_update

if __name__ == '__main__':
    try:
        app.run_server(debug=False)
    finally:
        teardown()
