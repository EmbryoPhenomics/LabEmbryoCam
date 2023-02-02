import cv2
from tqdm import tqdm
import time as timelib
from collections import deque
import threading
from more_itertools import pairwise
import numpy as np
import matplotlib.pyplot as plt

from camera_benchmark import CaptureBenchmark

feature_flags = {
    "framerate": cv2.CAP_PROP_FPS,
    "exposure": cv2.CAP_PROP_EXPOSURE,
    "contrast": cv2.CAP_PROP_CONTRAST,
    "width": cv2.CAP_PROP_FRAME_WIDTH,
    "height": cv2.CAP_PROP_FRAME_HEIGHT,
}

class OpenCV:
    def __init__(self, port=0, benchmark=True):
        self.benchmark = benchmark 
        self.benchmarker = CaptureBenchmark()

        try:
            self.camera = cv2.VideoCapture(port)
            self.is_released = False
        except:
            self.is_released = True
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
        self.camera.release()

    def get(self, name):
        return self.camera.get(feature_flags[name])

    def set(self, name, value):
        self.camera.set(feature_flags[name], value)

    def grab(self):
        ret, frame = self.camera.read()
        return frame

    def start_capture_stream(self, callback):
        self.shutdown = threading.Event()
        self.benchmarker.clear()
        self.benchmarker.record_start()

        while True:
            if self.shutdown.is_set():
                break
            else:
                ret, frame = self.camera.read()
                self.benchmarker.record_frame_time()

                if not ret:
                    self.benchmarker.record_incomplete()
                else:
                    callback(frame)
                    self.benchmarker.record_complete()

        self.benchmarker.record_end()

        if self.benchmark:
            self.benchmarker.print_log()

    def _display(self, frame):
        key = cv2.waitKey(1)
        if key == 27:
            self.shutdown.set()
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            reduction = 0.4
            width = int(frame.shape[1]*reduction)
            height = int(frame.shape[0]*reduction)
            dim = (width, height)
            cv2.imshow('Live Stream', frame)   

    def stream(self):
        self.start_capture_stream(self._display)

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
                    self.writer.write(frame)
                    self.pgbar.update(1)

    def acquire(self, path, time, in_memory):
        self.counter = 0
        self.acq_time = time

        # Start up frame consumer
        fps = int(self.get('framerate'))
        h, w, _ = self.grab().shape
        self.writer = cv2.VideoWriter(path, 0, fps, (w, h))

        self.frame_queue = deque()
        consume_thread = threading.Thread(target=self._write, args=(self.frame_queue,))
        consume_thread.start()

        print('Acquisition progress:')
        self.pgbar = tqdm(total=round(fps*time))

        # Start frame producer
        self.start_capture_stream(self._read)

        self.writer.release()
        self.pgbar.close()
