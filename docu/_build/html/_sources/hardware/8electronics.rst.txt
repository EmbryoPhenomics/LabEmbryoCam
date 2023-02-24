Electronics
==============

**Parts Required**

+------------------------------------------------------+--+-------------------------+
|﻿                                                     |n |Location                 |
+======================================================+==+=========================+
|**Parts**                                             |  |                         |
+------------------------------------------------------+--+-------------------------+
|Minitronics                                           |1 |minitronics mounting     |
+------------------------------------------------------+--+-------------------------+
|Stepper driver heatsinks                              |3 |minitronics step drivers |
+------------------------------------------------------+--+-------------------------+
|Limit switches                                        |3 |X, Y, Z switch mounts    |
+------------------------------------------------------+--+-------------------------+
|Limit switch cables                                   |3 |electronics              |
+------------------------------------------------------+--+-------------------------+
|Stepper motor cables                                  |3 |electronics              |
+------------------------------------------------------+--+-------------------------+
|Raspberry Pi 4 8GB                                    |1 |raspberry_pi_mount       |
+------------------------------------------------------+--+-------------------------+
|250 TB SSD                                            |1 |SSD mount                |
+------------------------------------------------------+--+-------------------------+
|Arduino Wingshield HAT                                |2 |electronics              |
+------------------------------------------------------+--+-------------------------+
|Arduino UNO for CNC, light and joystick               |3 |electronics              |
+------------------------------------------------------+--+-------------------------+
|USB A cables (0.5m) for Arduino to Pi connection      |3 |electronics              |
+------------------------------------------------------+--+-------------------------+
|SSD to USB 3.0 cable                                  |1 |electronic panel         |
+------------------------------------------------------+--+-------------------------+
|ATX power supply splitter                             |1 |atx_power_mount          |
+------------------------------------------------------+--+-------------------------+
|USB-C cables for connecting to ATX 5V output          |1 |Raspberry Pi             |
+------------------------------------------------------+--+-------------------------+
|Waterproof DC power cable set                         |1 |ATX -> Minitronics       |
+------------------------------------------------------+--+-------------------------+
|Industrial grade USB hub                              |1 |electronic panel         |
+------------------------------------------------------+--+-------------------------+
|CSI to HDMI Adapter for Pi HQ Camera                  |1 |Top of the Raspberry Pi  |
+------------------------------------------------------+--+-------------------------+
|Limit switch mounts                                   |1 |X and Y axes             |
+------------------------------------------------------+--+-------------------------+
|**3D prints**                                         |  |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_raspberry_pi_mount.stl                    |1 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_dual_arduino_mount_extended.stl           |1 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_minitronics_fan support(2).stl            |2 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_minitronics_fan fan_support(mirror)(2).stl|2 |                         |
+------------------------------------------------------+--+-------------------------+
|cable vibration dampener bottom.stl                   |2 |                         |
+------------------------------------------------------+--+-------------------------+
|cable vibration_dampener top.stl                      |2 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_atx_power_mount.stl                       |1 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_minitronics_mounting_bracket.stl          |1 |                         |
+------------------------------------------------------+--+-------------------------+
|electronics_ssd_mount.stl                             |1 |                         |
+------------------------------------------------------+--+-------------------------+



Electronics are mounted onto the rear of the LabEmbryoCam - onto specifically designed 3D printed mounting parts. All cabling to the LabEmbryoCam should run through the two vibration insulation brackets on the back and bottom of the instrument - to prevent environemntal vibration from impacting image acquisition.
 
 .. list-table:: 

    * - .. figure:: ../_static/electronics_CAD.png

           1.Electronics CAD render

      - .. figure:: ../_static/electronics_schematic.png

           2.Electronics connections

.. 
  :width: 750

.. figure:: 
  :width: 750

Lighting, joystick/buttons, and motor control are provided using microcontrollers, all running their own scripts which must be uploaded. See this guide for help on uploading the lighting, joystick and xyz motion scripts to microontrollers, using the freely available Arduino IDE: https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE

**Lighting controller**
Lighting is controlled via an Arduino UNO microcontroller, with a relatively simple script. The LuMini LED range 
provide a high and fairly uniform lighting pattern, at a low cost. However, there is significant scope for other 
lighting solution s. 
 
The script for uploading to the LED microcontroller is accessible in the LED_microcontroller folder in the LabEmbryoCam software

 
**Manual input controller**
Input from both the XY joystick and Z buttons is read by the manual input microntroller, also an Arduino UNO.
Both joystick and buttons connect directly to the manual input microcontroller.

The script to run on the manual input microcontroller is accessible within the LabEmbryoCam software in the joystick_microcontroller folder.

The wiring between the microcontroller, joystick and Z buttons are detailed in the joystick_microcontroller script.


**XYZ motion controller**
The LabEmbryoCam makes use of a CoreXY (https://en.wikipedia.org/wiki/CoreXY) style of motion control and this can be achieved using a range of different
microncontroller boards from both CNC and 3D printing suppliers. The Minitronics V2 board is used here because 
of a low cost and having integrated drivers (reducing setup complexity). More sophisticated boards would enable 
higher resolution (via microstepping) and quieter operation, but come at a higher cost.

Firmware and configuration files for the Minitronics board are accessible in the XYZ_microcontroller folder of the LabEmbryoCam software. The XYZ microcontroller is more sophisticated than the Arduino UNOs used for the lighting and manual input control, and requires some different settings when uploading the scripts using the Arduino IDE. Further information can be found here, in the 'Configuring Arduino' section: https://reprap.org/wiki/Minitronics_20


**Raspberry Pi**
A Raspberry Pi (RPi) 4 8GB can run the LabEmbryoCam smoothly, but it should also be possible to run on any other computer on which the Raspberry Pi camera is detected and Dash is supported. A heatsink and fan are suggested for optimal performance, and a powered USB hub to prevent excessive power draw from the USB ports leading to unreliable hardware connections. The camera should be connected to the RPi using an HDMI-CSI adapter - to enable sufficient distance from the camera to the RPi, mounted on the rear of the instrument. Follow enclosed instructions for mounting both the heatsink and CSI-HDMI adapter to the Raspberry Pi.

The RPi can be flashed with the operating system image found here, containing all dependancies installed. This can then 
be loaded onto a microSD card using the Rasperry Pi Imager - https://www.raspberrypi.com/software/.

The lighting, manual input, and XYZ microcontrollers should all be attached to the RPi, via the USB hub, which is itself 
then connected to a USB port of the RPi. All that is left, is to connect a mouse, keyboard and a monitor. Note that the 
RPi uses a microHDMI, so an adapter (included in the bill of materials is attached).

The Raspberry Pi is powered by the 5 V power supply from the ATX splitter, connected to a USB-C cable. This can be made by simply cutting a USB-C cable, stripping the 5V and earth cables and connecting these to the ATX 5V outputs.

.. figure:: ../static/electronics_schematic.png
  :width: 750


Continue to :doc:`9humidification-chamber`



