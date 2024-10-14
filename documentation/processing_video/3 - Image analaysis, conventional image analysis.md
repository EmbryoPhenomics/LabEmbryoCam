# 3 - Image analysis, conventional image analysis

The video captured from the LEC instrument is saved in `MJPG` encoded AVI files, which are compatible with almost all operating systems and image analysis software.  

You can analyse the video produced from the LEC instrument using conventional image analysis software, such as popular software applications like [ImageJ](https://imagej.net/ij/docs/index.html), but also through more focused computer vision tools such [HeartCV](https://github.com/EmbryoPhenomics/heartcv). 

We include here a simple script `examples/heartrate_estimation.py` for analysing a single timepoint video and extracting a cardiac rhythm (if there is one). However, we do encourage users to consult the [HeartCV](https://heartcv.readthedocs.io/en/latest/) documentation for more thorough guidance. 