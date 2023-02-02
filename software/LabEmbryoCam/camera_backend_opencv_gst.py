import cv2
from tqdm import tqdm
import time as timelib
from collections import deque
import threading
from more_itertools import pairwise
import numpy as np
import matplotlib.pyplot as plt
import subprocess as sp

from camera_benchmark import CaptureBenchmark
    
def gst_pipeline(width, height, fps):
    return f'nvarguscamerasrc sensor_id=0 aelock=true ! video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 ! nvvidconv ! appsink'

class OpenCV_GST:
    def __init__(self, benchmark=True):
        self.benchmark = benchmark 
        self.benchmarker = CaptureBenchmark()

        self.features = {
            'framerate': 30,
            'exposure': 100000,
            'width': 1920, 
            'height': 1080
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
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

    def grab(self):
        width = self.features['width']
        height = self.features['height']
        fps = self.features['framerate']

        cmd = gst_pipeline(width, height, fps)
        sp.call(str.split(f'v4l2-ctl -c exposure={self.features["exposure"]}'))
        cam = cv2.VideoCapture(cmd, cv2.CAP_GSTREAMER)
       
        ret, frame = cam.read()
        cam.release()
        return frame

    def start_capture_stream(self, callback):
        self.shutdown = threading.Event()
        self.benchmarker.clear()
        self.benchmarker.record_start()

        width = self.features['width']
        height = self.features['height']
        fps = self.features['framerate']

        cmd = gst_pipeline(width, height, fps)
        sp.call(str.split(f'v4l2-ctl -c exposure={self.features["exposure"]}'))
        cam = cv2.VideoCapture(cmd, cv2.CAP_GSTREAMER)
        
        while True:
            if self.shutdown.is_set():
                break
            else:
                ret, frame = cam.read()
                self.benchmarker.record_frame_time()

                if not ret:
                    self.benchmarker.record_incomplete()
                else:
                    callback(frame)
                    self.benchmarker.record_complete()

        self.benchmarker.record_end()
        cam.release()

        if self.benchmark:
            self.benchmarker.print_log()

    def _display(self, frame):
        key = cv2.waitKey(1)
        if key == 27:
            self.shutdown.set()
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            frame = cv2.resize(frame, (1280, 720))
            cv2.imshow('Live Stream', frame)
            self.pgbar.update(1)   

    def stream(self):
        self.pgbar = tqdm()
        self.start_capture_stream(self._display)
        self.pgbar.close()

    def _read(self, frame):
        if self.counter == 0:
            self.end_time = timelib.time() + self.acq_time

        current = timelib.time()
        if current <= self.end_time:
            self.frame_queue.append(frame)
            # reduction = 0.4
            # width = int(frame.shape[1]*reduction)
            # height = int(frame.shape[0]*reduction)
            # dim = (width, height)
            # cv2.imshow('Live Stream', frame)
            # cv2.waitKey(1)   

            self.counter += 1

        elif current > self.end_time:
            self.frame_queue.append(None)
            self.shutdown.set()
            
    def _write(self, frame_queue):
        while True:
            if len(frame_queue):
                frame = frame_queue.popleft()

                if frame is None:
                    break
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    self.writer.write(frame)
                    self.pgbar.update(1)

    def acquire(self, path, time):
        self.counter = 0
        self.acq_time = time

        # Start up frame consumer
        fps = int(self.get('framerate'))
        h, w = self.features['height'], self.features['width']
        self.writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'RGBA'), fps, (w, h))

        self.frame_queue = deque()
        consume_thread = threading.Thread(target=self._write, args=(self.frame_queue,))
        consume_thread.start()

        print('Acquisition progress:')
        self.pgbar = tqdm(total=round(fps*time))

        # Start frame producer
        self.start_capture_stream(self._read)

        self.writer.release()
        self.pgbar.close()

if __name__ == '__main__':
    cap = OpenCV_GST()
    cap.set('exposure', 13000)
    timelib.sleep(1)

    cap.acquire('./test.avi', 10)


