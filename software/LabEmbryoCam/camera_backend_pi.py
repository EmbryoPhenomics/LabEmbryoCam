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

from camera_benchmark import CaptureBenchmark

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

    def render(self, frame):
        p1, st, err = cv2.calcOpticalFlowPyrLK(self.first, frame, self.p0, None, **self.lk_params)

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

            for old, new, r in zip(good_old, good_new, rot):
                old, new = map(tuple, (old, new))

                rot_line_color = (0, 0, 255)
                if r > 0:
                    rot_line_color = (0, 255, 255)

                new = tuple(map(int, new))
                old = tuple(map(int, old))
                cv2.line(self.rot_mask, new, old, rot_line_color, 1)

            com_old = good_old.mean(axis=(0,))
            com_new = good_new.mean(axis=(0,))
            com_old, com_new = map(tuple, (com_old, com_new))  # for live view

            com_new = tuple(map(int, com_new))
            com_old = tuple(map(int, com_old))
            cv2.line(self.rot_mask, com_new, com_old, (255, 0, 0), 2)

            frame_view = vuba.bgr(frame)

        self.first = frame.copy()

        if p1 is None:
            self.p0 = p0.reshape(-1, 1, 2)
        else:
            self.p0 = good_new.reshape(-1, 1, 2)

        return np.hstack((frame_view, self.rot_mask))

# For live streaming via generator, requires context manager for teardown
class CaptureGenerator:
    def __init__(self, cam_cls):
        self.cam_cls = cam_cls

        self.shutdown = threading.Event()
        self.cam_cls.benchmarker.clear()

    def __enter__(self):
        print('Start.')
        # Command generation
        w, h, fps, ss, co = [self.cam_cls.features[key] for key in self.cam_cls.video_params]
        cmd = raspividyuv(w, h, fps, ss, co)

        # Initiation of raspiyuv
        self.process = sp.Popen(cmd.split(), stdout=sp.PIPE)
        atexit.register(self.process.terminate)

        # Remove first frame from the stream for timing accuracy
        first = self.process.stdout.read(w * h)
        self.cam_cls.benchmarker.record_start()

        while True:
            if self.shutdown.is_set():
                break
            else:
                self.process.stdout.flush()

                buffer = self.process.stdout.read(w * h)
                frame = np.frombuffer(buffer, dtype=np.uint8).reshape(h, w)

                self.cam_cls.benchmarker.record_frame_time()
                self.cam_cls.benchmarker.record_complete()
                yield frame

    def __exit__(self, exc_type, exc_value, exc_tb):
        print('Finished.')

        self.cam_cls.benchmarker.record_end()
        self.process.terminate()

        if self.cam_cls.benchmark:
            self.cam_cls.benchmarker.print_log()
            #self.benchmarker.plot_timings(self.benchmarker.data[2])


# Command generators for still and video capture

# Synchronous acquisition doesn't seem to output any data so using asynchronous method for still images
def raspiyuv(w, h, exposure, contrast):
    return f"raspiyuv -w {w} -h {h} --shutter {exposure} --contrast {contrast} --exposure off --output - --timeout 2000 --luma --nopreview"

def raspividyuv(w, h, fps, exposure, contrast):
    return f"raspividyuv -w {w} -h {h} --framerate {fps} --shutter {exposure} --contrast {contrast} --exposure off --output - --timeout 0 --luma --nopreview"

class PiCam:
    def __init__(self, benchmark=True, live_optflow=False):
        self.benchmark = benchmark 
        self.benchmarker = CaptureBenchmark()
        self.still_params = ['width', 'height', 'exposure', 'contrast']
        self.video_params = ['width', 'height', 'framerate', 'exposure', 'contrast']
        self.live_optflow = live_optflow

        if self.live_optflow:
            self.optflow = LiveOptFlow()

        self.features = {
            'framerate': 30,
            'exposure': 20,
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
        # Command generation
        w, h, fps, ss, co = [self.features[key] for key in self.video_params]
        cmd = raspividyuv(w, h, fps, ss, co)

        # Initiation of raspiyuv
        process = sp.Popen(cmd.split(), stdout=sp.PIPE)
        atexit.register(process.terminate)

        # Remove first frame from the stream for timing accuracy
        first = process.stdout.read(w * h)
        process.stdout.flush()
        
        # Retrieval of frame from memory
        buffer = process.stdout.read(w * h)
        frame = np.frombuffer(buffer, dtype=np.uint8).reshape(h, w)

        process.terminate() # Release the camera
        return frame

    def _capture_callback(self, callback):
        self.shutdown = threading.Event()
        self.benchmarker.clear()

        # Command generation
        w, h, fps, ss, co = [self.features[key] for key in self.video_params]
        cmd = raspividyuv(w, h, fps, ss, co)

        # Initiation of raspiyuv
        process = sp.Popen(cmd.split(), stdout=sp.PIPE)
        atexit.register(process.terminate)

        # Remove first frame from the stream for timing accuracy
        first = process.stdout.read(w * h)
        self.benchmarker.record_start()

        while True:
            if self.shutdown.is_set():
                break
            else:
                process.stdout.flush()

                buffer = process.stdout.read(w * h)
                frame = np.frombuffer(buffer, dtype=np.uint8).reshape(h, w)

                callback(frame)
                self.benchmarker.record_frame_time()
                self.benchmarker.record_complete()

        self.benchmarker.record_end()
        process.terminate()

        if self.benchmark:
            self.benchmarker.print_log()
            #self.benchmarker.plot_timings(self.benchmarker.data[2])

    def start_capture_stream(self, callback=None):
        if callback is not None:
            self._capture_callback(callback)
        else:
            return CaptureGenerator(self)

    def frame_to_bytes(self, frame):
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()  

    def _display(self, frame):
        key = cv2.waitKey(1)
        if key == 27:
            self.shutdown.set()
            cv2.destroyAllWindows()
        else:
            cv2.imshow('Live Stream', frame)   

    def stream(self):
        self.start_capture_stream(self._display)

    def _read(self, frame):
        if self.counter == 0:
            self.end_time = timelib.time() + self.acq_time

        if self.live_optflow and self.counter == 1:
            self.optflow.register_first(frame)

        current = timelib.time()
        if current <= self.end_time:
            self.frame_queue.append(frame)

            if self.live_optflow and self.counter > 1:
                live_view = self.optflow.render(frame)
                cv2.imshow('Live Stream', live_view)
                cv2.waitKey(1)

            self.pgbar.update(1)
            self.counter += 1

        elif current >= self.end_time:
            self.frame_queue.append(None)
            self.shutdown.set()
            cv2.destroyAllWindows()

    def _write(self, frame_queue):
        while True:
            if len(frame_queue):
                frame = frame_queue.popleft()

                if frame is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) # grayscale results in corrupted images on pi for some reason
                    self.writer.write(frame)
                else:
                    break

    def acquire(self, path, time, in_memory=True):
        self.counter = 0
        self.acq_time = time

        fps = int(self.get('framerate'))
            
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
            array = np.empty((len(self.frame_queue[:-1]), self.get('height'), self.get('width')), dtype=np.uint8)
            for i,frame in enumerate(self.frame_queue[:-1]):
                array[i,:,:] = frame[:]
            
            np.save(path, array)

            del self.frame_queue
            gc.collect()


        self.pgbar.close()
        
        
if __name__ == '__main__':
    cam = PiCam()
    cam.set('exposure', 20000)
        
    img = cam.grab()
    print(img.shape)
    print(img.mean(), img.ptp())
    cam.close()
    
    