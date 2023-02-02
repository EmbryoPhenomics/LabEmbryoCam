import vuba
import heartcv as hcv
import cv2
import os
import glob
import numpy as np
from natsort import natsorted, ns
from tqdm import tqdm
import matplotlib.pyplot as plt

# Parameters ------------------
video_path = '/media/z/DS/acquisition_48hrs_for_paper/A2/timepoint9.avi'
# -----------------------------

video = vuba.Video(video_path)

frames = video.read(
	start=0,
	stop=200,
	grayscale=True,
	low_memory=False
)

# Localisation
ept = hcv.epts(frames, fs=video.fps, binsize=8)  # Compute energy proxy traits (EPTs) - video is downsampled in this function.
roi, _ = hcv.identify_frequencies(video, ept)  # Supervision of localisation

# Segment all images to this cardiac region
segmented_frames = np.asarray(list(hcv.segment(frames, vuba.fit_rectangles(roi))))
v = segmented_frames.mean(axis=(1, 2))  # Compute MPV signal

peaks = hcv.find_peaks(v)  # Find peaks using AMPD

# Plot the results
time = np.asarray([i / video.fps for i in range(len(v))])

plt.plot(time, v, "k")
plt.plot(time[peaks], v[peaks], "or")
plt.xlabel("Time (seconds)")
plt.ylabel("Mean pixel value (px)")
plt.show()