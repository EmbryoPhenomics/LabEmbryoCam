**SOFTWARE**
============
  
The LabEmbryoCam app is built using Dash, a Python based framework from Plotly. The app enables control of the LabEmbryoCam instrument - including camera, XYZ position and lighting, and it enables the automated control of these during the course of an acquisition.

Additional analytical scripts are provided for integrating the acquired video for each XYZ position, and running various analyses including automated heartrate measurement and embryo size measurement.

Once you have powered on your system, you can enter the desktop environment of the LEC using the following password: `pi`. Once you have logged in, you can start the LabEmbryoCam (LEC) user interface by double clicking the icon on the desktop or in the Activities panel:

.. figure:: ../_static/starting-webserver.png
  :width: 550

A terminal window will automatically open followed by the browser with the webserver (user interface) loaded. We can now proceed with getting the hardware set up for running an experiment. When the LEC user interface first loads, it connects to the various hardware components automatically - give it a few seconds before interacting with it to allow this process to complete.

.. figure:: ../_static/global-ui.png
  :width: 650


The LEC user interface is divided into a number of sections

* A) **Experiment Settings** - for loading a configuration file to repopulate previously used settings.
* B) **Camera View** - for adjusting the camera, streaming the camera feed, and snapping still images.
* C) **XYZ controls and settings** - for homing the XYZ stage, and moving the optics carriage around.
* D) **XYZ Positions** - for populating a list of XYZ positions.
* E) **XYZ View** - for interacting with XYZ positions, and automatically generating positions for wells of multiwell plates.
* F) **Experiment setup** - for configuring and running experiments - either at a single positon, or multiple.
* G) **Experiment Progress** - for monitoring the progress of an experiment.

**INDEX**

.. toctree::
  
   SOFTWARE-INSTALLATION
   CAMERA-OPTIONS
   STAGE-OPTIONS
   SETTING-UP-EXPERIMENT
   ANALYSIS
