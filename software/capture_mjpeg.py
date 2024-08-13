#!/usr/bin/python3
import time
import cv2

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

from tqdm import tqdm

# IMX477
# 960x720 @ 120fps-pi4
# 1280x960 @ 100fps, 120fps-pi5
# 1920x1020 @ 50fps-pi4
# 2028x1080 @ 45fps-pi4, 50fps-pi5
# 1920x1440 @ 40fps-pi4
# 2028x1520 @ 35fps-pi4, 40fps-pi5
# 4000x3000 @ 10fps-pi4, 10fps-pi5
# 4056x3040 @ 10fps-pi5

# IMX296
# 1456x1080 @ 60fps-pi5

picam2 = Picamera2()
mode = picam2.sensor_modes[3]
print(mode)
config = picam2.create_video_configuration(
	sensor={"output_size": mode['size'], "bit_depth": mode['bit_depth']},
	main={"size": mode['size'], "format": 'RGB888'},
	lores={"size": (640, 480), "format": 'RGB888'},
	controls={
		'ExposureTime': 4000,
        'FrameRate': mode['fps'],
		'FrameDurationLimits': (1000, 1000000),
		'AwbEnable': 0,
		'AeEnable': 0,
		'ColourGains': (0,0)
	}		
)
picam2.configure(config)
print(picam2.camera_configuration())

#writer = cv2.VideoWriter('./test.avi', cv2.VideoWriter_fourcc(*"MJPG"), mode['fps'], mode['size'])

mjpeg_encoder = JpegEncoder(q=90)
mjpeg_encoder.framerate = mode['fps']
mjpeg_encoder.size = config["main"]["size"]
mjpeg_encoder.format = config["main"]["format"]
mjpeg_encoder.output = FileOutput("test.mjpeg")
mjpeg_encoder.start()

picam2.start()

start = time.time()
for i in tqdm(range(2000)):
    request = picam2.capture_request()
    mjpeg_encoder.encode("main", request)
    #main = request.make_array('main')
    
    #writer.write(main)
    
    if i % (mode['fps'] // 5) == 0:
        img = request.make_array("lores")
        #img = cv2.cvtColor(lores, cv2.COLOR_YUV420p2BGR)
        cv2.imshow('test', img)
        cv2.waitKey(1)

    request.release()

mjpeg_encoder.stop()
picam2.stop()
#writer.release()

'''
# Replay video
import imageio.v3 as iio

frames = iio.imiter("./test.mjpeg", plugin='pyav')
for frame in tqdm(frames):
    cv2.imshow('Video Playback', frame)
    cv2.waitKey(16)    
'''




