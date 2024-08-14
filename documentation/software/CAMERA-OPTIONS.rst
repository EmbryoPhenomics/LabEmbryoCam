**CAMERA-OPTIONS**
===============
Camera and lighting settings will need adjusting to suit your experimental system - species, study aim etc.  

Adjusting the camera and lighting settings can simply be achieved using the `Camera View` section of the user interface: 

.. figure:: ../_static/cam-setup.png
  :width: 450

Begin by choosing a resolution and these are dictated by the sensor modes available from the connected camera board. Currently there are two camera boards supplied with each LEC system: a global and a rolling shutter camera. The global shutter board only has one available sensor mode: 1456 x 1088 pixels @ 60 fps. The rolling shutter board has four different sensor modes: 1330 x 990 @ 120fps, 2028 x 1080 @ 50fps, 2028 x 1520 @ 40fps and 4032 x 3040 @ 10fps. Note that these framerates are a maximum achievable given low enough exposure times. 

A live stream can be initialised using 'Start/Stop Stream' - and a rotating cursor next to the button will indicate that the camera is running.

Use the live display to ascertain what changes, if any, may be required.

Note that the image you see, is smaller i.e. downsampled to fit on the display and to aid usability. You can Stop the stream and change to 'Desktop' if desired and when the stream is re-enabled a pop-up window will show you what the camera feed looks like in a larger window. You can also capture still images using the 'Snap' button, and these will be shown as interactive images in the 'Still Image' tab. 

You can then use the three tabs - LED, Exposure and Frame-rate, to make adjustments as required. However, changes to the camera's - exposure, frame rate, and resolution, should only be made when the 'Start/Stop Stream is deactivated. **Changes are only implemented when clicking 'Update'.**

The following are descriptions for each of the settings in the Camera View.

* **LED**: The percentage brightness of the LED ring light. Note that the lighting can also be adjusted by using the lighting mount up and down, and by screwing/unscrewing the darkfield adapter. The LED will by default go to sleep when not needed during an experiment.
* **Exposure**: The shutter speed at which the camera operates in milliseconds - 20 ms is a good starting point.
* **Analogue gain**: The analogue gain applied by the camera sensor, to be used too adjust the brightness of the images without affecting frame-rate. 
* **Frame-rate**: The frame-rate at which videos are captured, in frames per second.
* **Resolution**: Presets for resolution at which images will be captured - this is dependent on the available sensor modes for the connected camera board.

***For changes to the camera settings to take effect you must press the `Update` button at the bottom of the Camera Settings section.***

**Note**
There are two physical adjustable parameters on the lens bought frmo Phenomyx itself, the iris and the magnification. The upper adjustment ring is for adjusting the magnification and the lower adjustment ring is for adjusting the iris. If you change the magnification, the required distance between the sample in the multiwell plate and the lens will need to be changed as well - higher magnification requires the lens to be closer to the sample, it will also result in a darker image and perhaps even a requirement for more light (either by choosing a longer exposure, increasing the brightness of the LED, or adjusting the physical position of the light). Finally, by opening or closing the iris, the depth of field (i.e. depth of the sample that is in focus) can be adjusted. Typically greater depth of field is very welcome, but it comes at the cost of a darker image. So, a compromise is required and will need to be decided on a case-by-case basis.

Two lenses are supplied with the LEC bought from Phenomyx, a low magnification lens (specs) suitable for imaging whole wells in a multiwell plate and a higher magnification, variable zoom lens capable of imaging small specimens with the aid of auxillary lenses. The maximum field of view for the Hikrobot, low magnification lens is 83 x 62 mm (width x height), and the minimum field of view, i.e. at highest magnification, is 18 x 13.5 mm. By comparison, the higher magnification lens ...

Next to the 'Start/Stop Stream' button in the Camera View, is a 'Snap' button. This allows you to capture images dynamically while using the instrument. They are automatically saved in a 'snap-images' folder in the LEC application folder.

Still images are interactive, so you can zoom in and out, and move the image to find an improved view. Before starting the next step, you may wish to start the live video stream, if you haven't already, for easily finding the animals or subjects you wish to record using the LEC.

***If you would like to change the camera settings you must exit the live stream before doing this so that your changes can take effect. Then when you have finished choosing your desired setttings, press the `Update` button before starting the live stream again.***