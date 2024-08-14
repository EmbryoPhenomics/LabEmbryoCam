**ANALYSIS**
================

After running an experiment you are strongly encouraged to make a backup of your video and ensure you have a good record of the settings, and hardware setup. This should  include an image of a graticule slide captured at the same magnification as used in the experiment - if you intend to make spatial measurements. You can use the 'Snap' function to produce this.  

The analysis of your video will be highly dependant on study species, aims and the scale of the study. We provide a number of workflows, Python packages and guides on the processing and analysis of the types of video dataset produced using the LEC.

https://github.com/EmbryoPhenomics/LabEmbryoCam_V2/tree/main/documentation/processing_video

.. note::
	You can install the required dependency packages for these scripts using ``pip``::

		$ pip install -r requirements.txt

	The ``requirements.txt`` file is located in the same folder as the scripts.


Each of these bullet points needs to link to the scripts when its put on github.

- **Compiling Video**
	- A parallel python script for compiling individual timepoint videos for each position captured during the acquisition into one large concatenated video file.
- **Timepoint Viewer**
	- A python script that launches a simple GUI for scrolling through frames in an individual timepoint video.
- **Multi-timepoint Viewer**
	- A python script that launches a GUI for scrolling through the first frame from each timepoint video for a single position that was recorded.
- **Embryo Segmentation**
	- A python script that makes use of EmbryoCV_ for displaying embryo segmentation through a GUI. Note the segmentation is optimised for gastropod embryos.
- **Heart rate Estimation**
	- A python script that makes use of HeartCV_ for detecting a cardiac signal and consequently, the timings of individual heart beats.

.. _EmbryoCV: https://github.com/otills/embryocv
.. _HeartCV: https://github.com/EmbryoPhenomics/heartcv
