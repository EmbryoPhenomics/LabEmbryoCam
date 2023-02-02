.. _analysis:

Analysis Scripts
================

.. note::
	You can install the required dependency packages for these scripts using ``pip``::

		$ pip install -r requirements.txt

	The ``requirements.txt`` file is located in the same folder as the scripts.


Each of these bullet points needs to link to the scripts when its put on github.

- **Compiling Video**
	- A parallel python script for compiling individual timepoint videos into one large concatenated video file, for each position that was captured during an acquisition.
- **Timepoint Viewer**
	- A python script that launches a simple GUI for scrolling through frames in an individual timepoint video.
- **Multi-timepoint Viewer**
	- A python script that launches a GUI for scrolling through the first frame from each timepoint video for a single position that was recorded.
- **Embryo Segmentation**
	- A python script that makes use of EmbryoCV_ for displaying embryo segmentation through a GUI. Note only works on gastropod embryos.
- **Heart rate Estimation**
	- A python script that makes use of HeartCV_ for detecting a cardiac signal and consequently, the timings of individual heart beats.

.. _EmbryoCV: https://github.com/otills/embryocv
.. _HeartCV: https://github.com/EmbryoPhenomics/heartcv
