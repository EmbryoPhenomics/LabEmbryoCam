import vuba
import glob
import os
import cv2
from natsort import natsorted, ns

# Parameters ------------------
path_to_videos = '/media/z/DS/acquisition_48hrs_for_paper/A2'
window_resolution = (512, 512) # Change if you want a different image size
# -----------------------------

videos = glob.glob(os.path.join(path_to_videos, '*.avi'))
videos = natsorted(videos, alg=ns.IGNORECASE)

class TimepointViewer(vuba.BaseGUI):
    def __init__(self, videos, *args, **kwargs):
        self.videos = videos
        super(TimepointViewer, self).__init__(*args, **kwargs)

        self.trackbar("Timepoint", "timepoint", 0, len(self.videos))(self.read)

    @staticmethod
    def read(gui, val):
        if val >= gui.trackbars["timepoint"].min and val < gui.trackbars["timepoint"].max:
            gui['timepoint'] = val
            video = vuba.Video(gui.videos[val])
            gui.frame = video.read(index=0, grayscale=False)
            frame_proc = gui.process()
            video.close()
            cv2.imshow(gui.title, frame_proc)

gui = TimepointViewer(videos, title='Timepoint Viewer')

@gui.method
def main(gui):
    frame = gui.frame.copy()

    if window_resolution:
        frame = cv2.resize(frame, window_resolution)

    return frame

gui.run()
