import threading
import cv2
import os
import numpy as np
import time as timelib
from collections import namedtuple, deque
from tqdm import tqdm
import atexit

from vimba import *
from vimba.frame import *

from camera_benchmark import CaptureBenchmark

feature_flags = {
    "framerate": "AcquisitionFrameRate",
    "exposure": "ExposureTime",
    'contrast': 'BlackLevel',
    "width": "Width",
    "height": "Height",
}

camera = namedtuple("camera", ("name", "id"))

def setup_camera(camera):
    """
    Helper function for setting up an AVT camera for OpenCV.
    
    """
    opencv_formats = intersect_pixel_formats(
        camera.get_pixel_formats(), OPENCV_PIXEL_FORMATS
    )
    color_formats = intersect_pixel_formats(opencv_formats, COLOR_PIXEL_FORMATS)

    if color_formats:
        camera.set_pixel_format(color_formats[0])
    else:
        mono_formats = intersect_pixel_formats(opencv_formats, MONO_PIXEL_FORMATS)

        try:
            camera.set_pixel_format(mono_formats[0])
        except:
            raise Exception(
                "Camera does not support an OpenCV compatible format natively."
            )


class Vmb:
    def __init__(self, camera_id=None, benchmark=True):
        self.benchmark = benchmark 
        self.benchmarker = CaptureBenchmark()

        self.startup()

        if camera_id:
            self.start_camera(camera_id)
        else:
            cameras = self.cameras()
            self.start_camera(cameras[0].id)

        atexit.register(self.close) # if the program terminates unexpectedly

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
        self._close_camera()
        self.vmb._shutdown()

    def _close_camera(self):
        try:
            self.camera._close()
        except:
            pass  # No need to raise as only won't close
            # when no camera declared or camera is not opened

    def startup(self):
        self.vmb = Vimba.get_instance()
        self.vmb._startup()

    def cameras(self):
        cams = self.vmb.get_all_cameras()
        cameras = [camera(cam.get_name(), cam.get_id()) for cam in cams]
        return cameras

    def start_camera(self, camera_id):
        # If a camera is already opened, close it before initialising another
        self._close_camera()

        self.camera = self.vmb.get_camera_by_id(camera_id)
        self.camera._open()
        setup_camera(self.camera)

        # Enable fps adjustment and disable automatic exposure
        _features = {
            "ExposureAuto": "Off",
            "AcquisitionFrameRateEnable": True,
            "AcquisitionFrameRateMode": "Basic",
        }
        for f in _features:
            feat = self.camera.get_feature_by_name(feat_name=f)
            feat.set(_features[f])

    def get(self, name):
        return self.camera.get_feature_by_name(feat_name=feature_flags[name]).get()

    def set(self, name, value):
        try:
            feat = self.camera.get_feature_by_name(feat_name=feature_flags[name])
            min, max = feat.get_range()

            feat.set(value)
        except VimbaFeatureError:
            inc = feat.get_increment()

            if value <= min:
                val = min
            elif value >= max:
                val = max
            else:
                val = round(value / inc) * inc

            feat.set(val)
        except:
            raise ValueError(
                "Unable to set feature to value. Note that only features of type int or float are supported."
            )

    def grab(self):
        frame = self.camera.get_frame(timeout_ms=2000)        

        if frame.get_status() == FrameStatus.Complete:
            img = frame.as_numpy_ndarray()
        else:
            img = None

        return img

    def start_capture_stream(self, callback, buffer_size):
        self.shutdown = threading.Event()
        self.benchmarker.clear()
        self.benchmarker.record_start()

        try:
            self.camera.start_streaming(handler=callback, buffer_count=buffer_size)
            self.shutdown.wait()
        finally:
            self.camera.stop_streaming()

        self.benchmarker.record_end()

        # Force vimba to flush the frame queue after each stream
        self.camera._close()
        self.camera._open()

        if self.benchmark:
            self.benchmarker.print_log()

    def _display(self, camera: Camera, frame: Frame):
        key = cv2.waitKey(1)
        if key == 27:
            self.shutdown.set()
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        else:
            if frame.get_status() == FrameStatus.Complete:
                arr = frame.as_numpy_ndarray()
                reduction = 0.4
                width = int(arr.shape[1]*reduction)
                height = int(arr.shape[0]*reduction)
                dim = (width, height)
                cv2.imshow('Live Stream', cv2.resize(arr, dim, cv2.INTER_AREA))  


                self.benchmarker.record_frame_time()
                self.benchmarker.record_complete()
            else:
                self.benchmarker.record_incomplete()

        camera.queue_frame(frame)

    def stream(self):
        self.start_capture_stream(self._display, 50)

    def _write(self, queue):
        while True:
            if len(queue):
                frame = queue.popleft()
                if frame is None:
                    break

                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                self.writer.write(frame)
                self.pgbar.update(1)

    def _read(self, camera: Camera, frame: Frame):
        if self.counter == 0:
            self.end_time = timelib.time() + self.acq_time

        current = timelib.time()
        if current <= self.end_time:
            if frame.get_status() == FrameStatus.Complete:
                arr = frame.as_numpy_ndarray()
                self.frame_queue.append(arr)
                self.benchmarker.record_frame_time()
                self.benchmarker.record_complete()

                # reduction = 0.4
                # width = int(arr.shape[1]*reduction)
                # height = int(arr.shape[0]*reduction)
                # dim = (width, height)
                # cv2.imshow('Live Stream', arr)
                # cv2.waitKey(1)   

                self.counter += 1
            else:
                self.benchmarker.record_incomplete()

            camera.queue_frame(frame)

        elif current > self.end_time:
            self.frame_queue.append(None)
            self.shutdown.set()

    def acquire(self, path, time):
        self.counter = 0
        self.acq_time = time

        # Start up frame consumer
        fps = int(self.get('framerate'))
        h, w, _ = self.grab().shape
        self.writer = cv2.VideoWriter(path, 0, fps, (w, h)) # grayscale for mono alvium cams

        self.frame_queue = deque()
        consume_thread = threading.Thread(target=self._write, args=(self.frame_queue,))
        consume_thread.start()

        print("Acquisition progress:")
        self.pgbar = tqdm(total=round(fps * time))

        # Start frame producer
        self.start_capture_stream(self._read, 100)

        self.writer.release()
        self.pgbar.close()

