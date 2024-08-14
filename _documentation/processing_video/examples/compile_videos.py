import vuba
import cv2
import glob
from tqdm import tqdm
import os
from natsort import natsorted, ns
import multiprocessing as mp

# Parameters ----------------------
acquisition_folder = '/media/z/DS/acquisition_48hrs_for_paper'
output_folder = '/media/z/DS/acquisition_48hrs_for_paper'
output_codec = 'FFV1' # Lossless
cores = 4 # Cores to use for parallel compilation of video
# ---------------------------------

position_folders = glob.glob(os.path.join(acquisition_folder, '*'))

# Exclude capture and time data
position_folders = [e for e in position_folders if os.path.isdir(e)]

position_names = [str.split(folder, '/')[-1] for folder in position_folders]
position_acq_length = {}
for p,f in zip(position_names, position_folders):
	position_acq_length[p] = len(glob.glob(os.path.join(f, '*.avi')))

position_pg = {}
for i, p in enumerate(position_names): 
    position_pg[p] = tqdm(total=position_acq_length[p], desc=p, position=i+1)

tqdm.set_lock(mp.RLock())

def compile_timepoints(folder):
	videos = glob.glob(os.path.join(folder, '*.avi'))
	videos = natsorted(videos, alg=ns.IGNORECASE)

	position_name = str.split(folder, '/')[-1]
	pgbar = position_pg[position_name]

	first_video = vuba.Video(videos[0])

	writer = vuba.Writer(
		os.path.join(output_folder, f'{position_name}.avi'),
		first_video, codec=output_codec
	)

	first_video.close()

	for video in videos:
		video = vuba.Video(video)

		for frame in video.read(start=0, stop=len(video), grayscale=False):
			writer.write(frame)

		video.close()
		pgbar.update(1)

	writer.close()

with mp.Pool(processes=cores) as pool:
	pool.map(compile_timepoints, position_folders)