import numpy as np
import matplotlib.pyplot as plt
import time


class CaptureBenchmark:
    '''
    Simple benchmark tool for measuring performance of acquisitions on 
    different camera platforms.

    '''
    def __init__(self):
        self.start = self.end = None
        self.complete = self.incomplete = 0
        self.frame_times = []
        self.data = ()

    def clear(self):
        self.start = self.end = None
        self.complete = self.incomplete = 0
        self.frame_times = []
        self.data = ()

    def record_start(self):
        self.start = time.time()

    def record_end(self):
        self.end = time.time()

    def record_frame_time(self):
        self.frame_times.append(time.time())

    def record_incomplete(self):
        self.incomplete += 1

    def record_complete(self):
        self.complete += 1

    def compute_timings(self):
        frame_times = np.asarray(self.frame_times)
        frame_timings = frame_times[1:] - frame_times[:-1]

        total = self.end - self.start
        capture = frame_times[-1] - frame_times[0]
        ancillary = total - capture

        self.data = ((total, capture, ancillary), (self.complete, self.incomplete), frame_timings)
        return self.data

    def print_log(self):
        ((total, capture, ancillary), (complete, incomplete), ft) = self.compute_timings()

        print("---------------------------------------------------------")
        print("Acquisition log:")
        print("---------------------------------------------------------")
        print(f"Total time: {total}")
        print(f"Time to acquire frames: {capture}")
        print(f"Time for ancillary processes: {ancillary}")
        print(f"Complete / Incomplete frames: {(complete, incomplete)}")
        print("Frame timings:")
        print(f"Mean: {ft.mean()}, Min: {ft.min()}")
        print(f"Max: {ft.max()}, SD: {np.std(ft)} \n")
        print("---------------------------------------------------------")

    def plot_timings(self, frame_timings, path=None):
        fig = plt.figure()

        plt.hist(x=frame_timings, bins='auto', alpha=0.7, rwidth=0.85)
        plt.grid(axis='y', alpha=0.75)
        plt.xlabel('Frame timings')
        plt.ylabel('Frequency')

        if path is not None:
            fig.savefig(path, dpi=fig.dpi)
        else:
            plt.show()

