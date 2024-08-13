# Acquisition class instance for handling timelapse acquisitions
import time
import threading
import pandas as pd
import os
import datetime
import emails
import multiprocessing as mp
import cv2
import re

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

    try:
        if email.isLoggedIn:
            outfiles = [] 

            if isinstance(paths, list):
                for file in paths:
                    video = cv2.VideoCapture(file)
                    _, frame = video.read()
                    new_file = re.sub('.mkv', '.png', file)
                    cv2.imwrite(new_file, frame)
                    video.release()

                    outfiles.append(new_file)
            else:
                video = cv2.VideoCapture(paths)
                _, frame = video.read()
                new_file = re.sub('.mkv', '.png', paths)
                cv2.imwrite(new_file, frame)
                video.release()

                outfiles.append(new_file)

            text = f"""\
            LEC update: Timepoint {timepoint}

            No. of positions imaged: {len(paths)}

            See attached files for still images of positions at this timepoint."""

            email.send(f'LEC update: timepoint {timepoint}', text, outfiles)

            for file in outfiles:
                os.remove(file)
    finally:
        email.close()

class Acquisition:
    def __init__(self):
        self.acquiring = False

    def acquire(self, *args, **kwargs):
        '''
        Main acquisition loop for acquiring timelapse video at different XYZ positions

        Parameters
        ----------
        folder : str
            File path to folder in which to save video.
        positions : str
            Number of positions to acquire video for, either 'Single' or 'Multiple'. If
            'Single' then only the current position will be recorded, else the stage will 
            move between positions and capture video for each.
        timepoints : int
            Number of timepoints to iterate the acquisition loop over.
        interval : int or float
            Length of time between timepoints (minutes).
        capture_length : int or float
            Duration of video capture at each timepoint and each position (seconds).

        exposure : int or float
            Shutter speed in micro-seconds.
        fps : int or float
            Frame-rate of video capture
        sensor_mode : int
            Camera sensor mode index, this is specific to a given camera model and the sensor driver
            as to what modes are available. For more info check: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
            and section 4.2.2.3

        stage : Object
            Class instance of the Hardware class in the 'xyz' module for controlling the XYZ stage.
        leds : Object
            Class instance of the HardwareBrightness class in the 'leds' module for controlling LEDS brightness.
        light_auto_dim : bool
            Whether to dim lights between timepoints.

        exp_log : Object
            Class instance for recording information regarding acquisition progress.
        
        xyz_coords : Object
            XYZ coordinate class derived from 'xyz' module.

        email : Object
            Email class instance derived from 'email' module.

        '''
        thread = threading.Thread(target=self._acquire, args=args, kwargs=kwargs)
        thread.start()


    def _acquire(self,
        folder, positions, timepoints, interval, capture_length, # Acquisition parameters
        camera, exposure, fps, sensor_mode, analogue_gain, # Camera settings
        stage, leds, light_auto_dim, # Hardware instances and settings
        exp_log, # Ancillary instances
        xyz_coords, # XYZ coordinates
        email): # Email class

        self.shutdown = threading.Event()
        exp_log.clear()
        
        self.acquiring = True

        # Timelapse recording for a single position
        if positions == 'Single':
      
            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            if not light_auto_dim:
                leds.set(0)

            time.sleep(1)

            x,y,z,label = xyz_coords.get_current()

            exp_log.startup([label], timepoints)
            time_data = []
            paths = []
            for t in range(timepoints):
                if self.shutdown.is_set():
                    self.acquiring = False
                    print('Exiting acquisition...')
                    return          

                print(f'Acquiring footage for timepoint {t+1}...')
                
                # Turn leds on
                leds.set(LED_VALUE)
                time.sleep(1)

                path = os.path.join(folder, f'{label}_timepoint{t+1}.mkv')
                paths.append(path)

                # Acquire footage
                t1 = time.time()

                timings = camera.video_capture(path, capture_length, exposure=exposure, fps=fps, analogue_gain=analogue_gain, sensor_mode=sensor_mode)
                ((total, capture, ancillary), (complete, incomplete), ft) = timings
                timepointData = (total, capture, ancillary, incomplete, str(t), 0, ft.mean(), ft.min(), ft.max())
                time_data.append(timepointData)
                t2 = time.time()

                exp_log.update(label, t, str(datetime.datetime.fromtimestamp(t2)))

                # Turn leds off
                if not light_auto_dim:
                    leds.set(0) 

                # Send progress updates
                if email.isLoggedIn:
                    email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*[timepointData, ]), path))
                    email_proc.start()

                t2 = time.time()
                acqTime = t2 - t1
                print(f'Sleep time: {interval*60 - acqTime}')
                sleep_time = interval*60 - acqTime
                
                for i in range(round(sleep_time)):
                    if self.shutdown.is_set():
                        leds.set(LED_VALUE)
                        self.acquiring = False
                        print('Exiting acquisition...')
                        return          
                    
                    time.sleep(1)    

        elif positions == 'Multiple':
            if interval == 0:
                raise ValueError('Cannot have no acquisition interval when acquiring footage for multiple positions.')

            labels = xyz_coords.labels
            xy_data = [dict(x=x, y=y, z=z) for x,y,z in zip(xyz_coords.xs, xyz_coords.ys, xyz_coords.zs)]

            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            if not light_auto_dim:
                leds.set(0)

            time.sleep(1)

            # Creation of filepaths
            paths = {}
            for replicate in labels:
                paths[replicate] = []
                replicate_path = os.path.join(folder, replicate + '/')

                if not os.path.exists(replicate_path):
                    os.makedirs(replicate_path)

                for t in range(timepoints):
                    timepoint_path = os.path.join(replicate_path, f'timepoint{t+1}.mkv')
                    paths[replicate].append(timepoint_path)

            exp_log.startup(labels, timepoints)

            print('[INFO] Starting acquisition for multiple positions...')
            time_data = []
            for t in range(timepoints):
                print(f'Acquiring footage for timepoint {t+1}...')

                # Turn leds on
                leds.set(LED_VALUE)
                time.sleep(1)
              
                t1 = time.time()
                timepointPaths = []
                timepointData = []
                for label,pos in zip(labels, xy_data):
                    if self.shutdown.is_set():
                        self.acquiring = False
                        print('Exiting acquisition...')
                        return          

                    # Position move
                    x,y,z = (pos['x'], pos['y'], pos['z'])
                    stage.moveXY(x,y,z)

                    # Acquire footage
                    path = paths[label][t]
                    timepointPaths.append(path)

                    timings = camera.video_capture(path, capture_length, exposure=exposure, fps=fps, analogue_gain=analogue_gain, sensor_mode=sensor_mode)
                    ((total, capture, ancillary), (complete, incomplete), ft) = timings
                    timepoint_data = (total, capture, ancillary, incomplete, str(t), label, ft.mean(), ft.min(), ft.max())
                    
                    time_data.append(timepoint_data)
                    timepointData.append(timepoint_data)

                    exp_log.update(label, t, datetime.datetime.fromtimestamp(t1))

                exp_log.export(os.path.join(folder, 'time_data.csv'))

                # Turn leds off
                if not light_auto_dim:
                    leds.set(0)     

                # Send progress updates
                if email.isLoggedIn:
                    email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*timepointData), timepointPaths))
                    email_proc.start()

                t2 = time.time()
                acqTime = t2 - t1
                print(f'Sleep time: {interval*60 - acqTime}')
                sleep_time = interval*60 - acqTime
                
                for i in range(round(sleep_time)):
                    if self.shutdown.is_set():
                        leds.set(LED_VALUE)
                        self.acquiring = False                        
                        print('Exiting acquisition...')
                        return          
                    
                    time.sleep(1)    
                           
        leds.set(LED_VALUE)

        print('Completed acquisition.')
        df = pack_results(zip(*time_data))
        df.to_csv(os.path.join(folder, 'capture_data.csv'))

        if email.isLoggedIn:
            text = f"""\
            LEC update: Completed acquisition.
            """

            email.login(email.username, email.password)
            email.send(f'LEC update: Completed acquisition.', text, None)
            email.close()

        self.stop()
        self.acquiring = False


    def stop(self):
        '''
        Stop acquisition loop if it's running.
        '''
        if self.acquiring:
            self.shutdown.set()
            


