import vuba

# Parameters ------------------
video_path = '/media/z/DS/acquisition_48hrs_for_paper/A2/timepoint1.avi'
timepoint = 0
seconds_per_timepoint = 10
# -----------------------------

video = vuba.Video(video_path)

start = (timepoint * (seconds_per_timepoint * video.fps))
stop = ((timepoint + 1) * (seconds_per_timepoint * video.fps))

gui = vuba.VideoGUI(
	video=video, 
	title='Individual timepoint viewer', 
	indices=(start, stop))

@gui.method
def main(gui):
    frame = gui.frame.copy()
    return frame

gui.run()
video.close()