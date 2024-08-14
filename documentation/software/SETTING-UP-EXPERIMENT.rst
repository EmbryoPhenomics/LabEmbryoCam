**SETTING-UP-EXPERIMENT**
=================

The acquisition parameters can be found at the bottom of the page of the user interface in the Acquisition section:

.. figure:: ../_static/expt-setup.png
  :width: 450

Here are descriptions for each acquisition parameter:

* **Number of positions**: Whether you would like to capture footage for only the current position (‘Single’) or all the XYZ positions you have recorded (‘Multiple’).
* **Number of timepoints**: How many acquisition iterations you would like the system to complete. An iteration consists of capturing footage for the specified positions. Setting the acquisition interval allows us to set this process to complete every X minutes, where X would be the acquisition interval.
* **Acquisition interval**: How long to wait between each timepoint in minutes - you must consider how long it will take for each acquisition to complete, or risk the previous acquisition not finishing before the next starts.
* **Acquisition length**: How long to acquire video for each position, at each timepoint.
* **Driver and Folder selection**: The full file path to the directory where you would like to save video. This should be selected using the Select button and navigating the browser that pops up.
* **Turn off light between timepoints**: Whether to turn the LED light ring off between timepoints during an acquisition. 

Once you have added in your desired acquisition parameters, you can now start an acquisition using the Start acquisition button.

**Note**
If you would like to receive email updates and your LEC is connected to a network via WiFi or ethernet, then you simply need to edit the `app_config.json` folder located in the source code folder (`/home/pi/LabEmbryoCam_V2/software/`), with the following changes:

```
	"emails": "on", # Change to "off" if you would like to turn off email updates.
	"email_username": "username@gmail.com", 
	"email_password": "password", # Must be an app password
```

The email updates module for the LEC uses gmail so you will need to register an account with gmail and create an app password (see https://support.google.com/mail/answer/185833?hl=en-GB). You will need to specify this app password in the `email_password` argument. 

Finally, progress of the experiment will be shown at the bottom of the user interface in the 'Experiment Progress' section. This enables tracking the progress of an experiment.

.. figure:: ../_static/expt-progress.png
  :width: 450