import vuba
import heartcv as hcv
import cv2
import os
import glob
import numpy as np
from natsort import natsorted, ns
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys

from embryocv import locateEmbryo

# Parameters ------------------
video_path = '/media/z/DS/acquisition_48hrs_for_paper/A2/timepoint9.avi'
# -----------------------------

video = vuba.Video(video_path)

frames = list(video.read(0, len(video), grayscale=False))

gui = vuba.FramesGUI(
    frames=frames, 
    title='Embryo Segmenation'
)

@gui.method
def main(gui):
    frame = gui.frame.copy()

    frame = cv2.resize(frame, (512, 512))

    outline = locateEmbryo(frame)
    vuba.draw_contours(frame, outline, -1, (0,255,0), 1)

    return frame

gui.run()
video.close()