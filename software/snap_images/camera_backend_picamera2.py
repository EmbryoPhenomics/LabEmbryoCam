import cv2
import picamera2
from tqdm import tqdm
import time

import cv2 
import time as timelib
from tqdm import tqdm
from collections import deque
import numpy as np
import threading
import re
import pandas as pd
import subprocess as sp
import atexit
import gc
import math
import vuba

from camera_benchmark import CaptureBenchmark

font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.5
fontColor = (255,255,255)
lineType = 1

class LiveOptFlow:
    def __init__(self):
        self.feature_params = dict(
            maxCorners=500,
            qualityLevel=0.001,
            minDistance=0,
            blockSize=7,
            useHarrisDetector=0,
            k=0.4,
        )

        # Parameters for lucas kanade optical flow
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
        )

    def register_first(self, frame):
        self.first = frame
        self.p0 = cv2.goodFeaturesToTrack(frame, mask=None, **self.feature_params)
        self.rot_mask = cv2.cvtColor(np.zeros_like(frame), cv2.COLOR_GRAY2BGR)
        self.point_log = deque(maxlen=5) # Max point memory of 5

    def render(self, frame):
        p1, st, err = cv2.calcOpticalFlowPyrLK(self.first, frame, self.p0, None, **self.lk_params)
    
        frame_view = vuba.bgr(frame)
        if p1 is None:
            good_new = None
            good_old = None
        else:    
            good_new = p1[st == 1]
            good_old = self.p0[st == 1]

        if good_new is not None and good_old is not None:
            ind_diff = good_new - good_old
            rot = np.asarray(
                list(map(lambda vals: math.atan2(*np.flip(vals)), ind_diff))
            ) # compute angles of rotation                

            self.point_log.append((good_old, good_new, rot, ind_diff))
            
            for (good_old, good_new, rot, diff) in self.point_log:
                for old, new, r, d in zip(good_old, good_new, rot, diff):
                    if math.sqrt(d[0]**2 + d[1]**2) < 0.25:
                        continue
                    
                    old, new = map(tuple, (old, new))

                    rot_line_color = (0, 255, 0)
                    # if r > 0:
                    #     rot_line_color = (0, 255, 255)

                    new = tuple(map(int, new))
                    old = tuple(map(int, old))
                    cv2.line(frame_view, new, old, rot_line_color, 1)

                if len(good_old) and len(good_new):
                    com_old = good_old.mean(axis=(0,))
                    com_new = good_new.mean(axis=(0,))
                    com_old, com_new = map(tuple, (com_old, com_new))  # for live view

                    com_new = tuple(map(int, com_new))
                    com_old = tuple(map(int, com_old))
                    cv2.line(frame_view, com_new, com_old, (255, 0, 0), 2)

        self.first = frame.copy()

        if p1 is None:
            self.p0 = self.p0.reshape(-1, 1, 2)
        else:
            self.p0 = good_new.reshape(-1, 1, 2)

        #return np.vstack((frame_view, self.rot_mask))
        #resized_mask = cv2.resize(self.rot_mask, (round(self.rot_mask.shape[1]/3), round(self.rot_mask.shape[0]/3)))
        #white_border = np.full((resized_mask.shape[0]+2, resized_mask.shape[1]+2, 3), 255).astype(np.uint8)
        
        #frame_view[:white_border.shape[0], :white_border.shape[1]] = white_border[:]
        #frame_view[:resized_mask.shape[0], :resized_mask.shape[1]] = resized_mask[:]
        #cv2.putText(frame_view, 'Optical Flow Live Stream',
        #            tuple(map(int, (0.01*frame_view.shape[1], 0.02*frame_view.shape[0]))),
        #            font, fontScale, fontColor, lineType)
        return frame_view

class CaptureGenerator:
    def __init__(self, cam_cls):
        self.cam_cls = cam_cls
        
        self.cam_cls.start_camera()
        self.shutdown = threading.Event()
        self.cam_cls.benchmarker.clear()
        print('Cleared benchmark and created shutdown')

    def __enter__(self):
        print('Start.')

        w, h, fps, ss, co = [self.cam_cls.features[key] for key in self.cam_cls.video_params]
        print('Retrieved video parameters')

        # Stop stream and interrupt with new controls and config
        self.cam_cls.camera.stop()
        cfg = self.cam_cls.configuration(w, h)
        print('Created video config', cfg)
        self.cam_cls.camera.configure(cfg)
        print('Configured camera')
        self.cam_cls.camera.start()
        print('Initiated camera')              
               
        self.cam_cls.camera.set_controls({
            'FrameRate': fps, 
            'ExposureTime': ss, 
            'AeEnable': 0,
            'AwbEnable': 0,
            #'Contrast': co
        })
        print('Set camera controls')
        
        self.cam_cls.benchmarker.record_start()
        print('Started benchmarking')
        
        print(self.shutdown.is_set())
        while True:
            if self.shutdown.is_set():
                break
            else:
                frame = self.cam_cls.camera.capture_array()
                frame = np.flip(frame, axis=1)
                self.cam_cls.benchmarker.record_frame_time()
                
                self.cam_cls.benchmarker.record_complete()
                yield frame

    def __exit__(self, exc_type, exc_value, exc_tb):
        print('Finished.')              
        self.cam_cls.benchmarker.record_end()
        self.cam_cls.camera.stop()
        self.cam_cls.close()

        if self.cam_cls.benchmark:
            self.cam_cls.benchmarker.print_log()


class PiCam2():
    def __init__(self, benchmark=True, live_optflow=False):
        self.benchmark = benchmark 
        self.benchmarker = CaptureBenchmark()
        self.video_params = ['width', 'height', 'framerate', 'exposure', 'contrast']
        self.live_optflow = live_optflow

        if self.live_optflow:
            self.optflow = LiveOptFlow()
                    
        self.is_streaming = False

        self.features = {
            'framerate': 30,
            'exposure': 20000, # in u-ms, *1000 for ms
            'contrast': 0,
            'width': 640, 
            'height': 480
        }
        
        timelib.sleep(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
        if self.camera:
            self.camera.close()
        return None

    def get(self, name):
        try:
            value = self.features[name]
        except KeyError:
            raise KeyError('Feature not currently supported.')
        except:
            raise

        return value

    def set(self, name, value):
        try:
            self.features[name] = value
        except KeyError:
            raise KeyError('Feature not currently supported.')
        except:
            raise

    def configuration(self, w, h):
        cfg = self.camera.create_video_configuration(
            main={'size': (w, h)}, 
            raw={'size': (w, h)}, 
            #encode='h264'
        )
        return cfg
        
    def start_camera(self):
        try:
            self.camera = picamera2.Picamera2()
            self.is_released = False
        except:
            self.is_released = True
            raise

    def grab(self):
        # Command generation
        w, h, fps, ss, co = [self.features[key] for key in self.video_params]
        
        self.start_camera()
                
        # Stop stream and interrupt with new controls and config
        #self.camera.stop()
        cfg = self.configuration(w, h)
        self.camera.configure(cfg)
        self.camera.start()
               
        self.camera.set_controls({
            'FrameRate': fps, 
            'ExposureTime': ss, 
            'AeEnable': 0,
            'AwbEnable': 0,
            #'Contrast': co
        })
        
        frame = self.camera.capture_array()
        print(frame.shape)
        self.camera.stop()
        self.close()

        return frame

    def _capture_callback(self, callback):
        self.start_camera()
        self.shutdown = threading.Event()
        self.benchmarker.clear()
        print('Cleared benchmark and created shutdown')

        w, h, fps, ss, co = [self.features[key] for key in self.video_params]
        print('Retrieved video parameters')

        # Stop stream and interrupt with new controls and config
        self.camera.stop()
        cfg = self.configuration(w, h)
        print('Created video config', cfg)
        self.camera.configure(cfg)
        print('Configured camera')
        self.camera.start()
        print('Initiated camera')              
               
        self.camera.set_controls({
            'FrameRate': fps, 
            'ExposureTime': ss, 
            'AeEnable': 0,
            'AwbEnable': 0,
            #'Contrast': co
        })
        print('Set camera controls')
        
        self.benchmarker.record_start()
        print('Started benchmarking')
        
        print(self.shutdown.is_set())
        while True:
            if self.shutdown.is_set():
                break
            else:
                frame = self.camera.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
                frame = np.flip(frame, axis=1)

                self.benchmarker.record_frame_time()

                callback(frame)
                self.benchmarker.record_complete()
    
        print('Cleaning up.')

        self.benchmarker.record_end()
        self.camera.stop()
        self.close()

        if self.benchmark:
            self.benchmarker.print_log()

    def start_capture_stream(self, callback=None):
        if callback is not None:
            self._capture_callback(callback)
        else:
            return CaptureGenerator(self)

    def frame_to_bytes(self, frame):
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes() 
         
    def _display(self, frame):
        if self.live_optflow and self.counter == 1:
            self.optflow.register_first(frame)

        if self.live_optflow and self.counter % 120 == 0 and self.counter > 1:
            self.optflow.register_first(frame)

        cv2.waitKey(1)
        if self.key == 27:
            self.shutdown.set()
            cv2.destroyAllWindows()
        else:
            if self.live_optflow and self.counter > 1:
                live_view = self.optflow.render(frame)
                cv2.imshow('Live Stream', live_view)
            elif not self.live_optflow and self.counter > 1:
                cv2.imshow('Live Stream', frame)
            self.counter += 1
            
    def _read(self, frame):
        if self.counter == 0:
            self.end_time = timelib.time() + self.acq_time

        if self.live_optflow and self.counter == 1:
            self.optflow.register_first(frame)

        current = timelib.time()
        if current <= self.end_time:
            self.frame_queue.append(frame)

            if self.live_optflow and self.counter > 1 and self.counter % self.live_skip_interval == 0:
                live_view = self.optflow.render(frame)
                cv2.imshow('Live Stream', live_view)
                cv2.waitKey(1)
            elif not self.live_optflow and self.counter > 1 and self.counter % self.live_skip_interval == 0:
                cv2.imshow('Live Stream', frame)
                cv2.waitKey(1)

            self.pgbar.update(1)
            self.counter += 1

        elif current >= self.end_time:
            self.frame_queue.append(None)
            self.shutdown.set()
            cv2.destroyAllWindows()
    
    def stream(self):
        try:
            self.key = None
            self.is_streaming = True
            self.counter = 0
            self.start_capture_stream(self._display)
        finally:
            self.is_streaming = False

    def _write(self, frame_queue):
        while True:
            if len(frame_queue):
                frame = frame_queue.popleft()

                if frame is not None:
                    self.writer.write(frame)
                    self.pgbar.update(1)
                else:
                    break

    def acquire(self, path, time, in_memory=True):
        self.counter = 0
        self.acq_time = time

        fps = int(self.get('framerate'))
        self.live_skip_interval = fps // 10
        if self.live_skip_interval == 0:
            self.live_skip_interval = fps # set to update once every second if fps very low
    
        if in_memory:
            self.frame_queue = []
        else:
            self.writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MPEG"), fps, (self.get('width'), self.get('height'))) # MJPG fastest, albeit lossy. Raw is 10-20% slower.
          
            self.frame_queue = deque()
            consume_thread = threading.Thread(target=self._write, args=(self.frame_queue,))
            consume_thread.start()

        print('Acquisition progress:')
        self.pgbar = tqdm(total=round(fps*time))

        # Start frame producer
        self.start_capture_stream(self._read)

        if not in_memory:
            self.writer.release()
        else:
            array = np.empty((len(self.frame_queue[:-1]), self.get('height'), self.get('width'), 3), dtype=np.uint8)
            for i,frame in enumerate(self.frame_queue[:-1]):
                array[i,:,:,:] = frame[:]
            
            np.save(path, array)

            del self.frame_queue
            gc.collect()


        self.pgbar.close()

if __name__ == '__main__':
    cam = PiCam2()
    cam.set('exposure', 5000)
            
    cam.acquire('./test.avi', time=10, in_memory=True)
    
    timelib.sleep(1)
       
    cam.acquire('./test.avi', time=10, in_memory=False)
    
    cam.close()
