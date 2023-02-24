.. _software-installation:

Software installation
=====================
LabEmbryoCam software is a Dash based webserver. It is tested on Raspberry Pi4 8GB single board computers, but could run on other Raspberry Pi models, or other systems with appropriate camera drivers and support for dependencies. The Jetson single board computers with appropriate Raspberry Pi HQ cameras is capable of running the LabEmbryoCam effectively.

A disk image containing the Raspbian OS with all necessary prerequisites and the LabEmbryoCam preinstalled. The disk image can be written to a microSD card using Rasberry Pi Imager - https://www.raspberrypi.com/software/. LabEmbryoCam is an active project and users are encouraged to download the most recent version of the software from https://github.com/EmbryoPhenomics/LabEmbryoCam.

Within the LabEmbryoCam software there is a 'requirements.txt' file and this lists all of the dependencies required. If starting with a new Raspian OS (rather than using the disk image from above), these dependencies will need to be installed.

You can install the required dependency packages for the LabEmbryoCam using ``pip``::

    $ pip install -r requirements.txt

The ``requirements.txt`` file for the LabEmbryoCam webserver is located in the same folder as the LabEmbryoCam folder



