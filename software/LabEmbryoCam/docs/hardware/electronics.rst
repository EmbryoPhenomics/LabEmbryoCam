Electronics
========


.. list-table::
   :widths: 4 3 3 5
   :header-rows: 1

   * - Part
     - Number
     - Details
     - Location
   * - **Aluminium extrusion**
     -
     -
     -
   * - 2040 extrusion
     - 4
     - 420mm
     - Uprights
   * - 2040 extrusion
     - 8
     - 336 mm
     - Front-back laterals
   * - Noctua fan mounts
     - 2
     - 356 mm
     - Cross beams

.. figure:: _build/html/_images/electronics_schematic.png
  :width: 250

**Lighting controller**
Lighting is controlled via an Arduino UNO microcontroller, with a relatively simple script. The LuMini LED range 
provide a high and fairly uniform lighting pattern, at a low cost. However, there is significant scope for other 
lighting solutions.

The script for uploading to the LED microcontroller is accessible here: ....

The wiring is: ....

See Arduino guide for help on uploading scripts to microontrollers: https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE

**Manual input controller**
Input from both the XY joystick and Z buttons is read by the manual input microntroller, also an Arduino UNO.
Both joystick and buttons connect directly to the manual input microcontroller.

The script for uploading to the manual input microcontroller is accessible here: ....

The wiring is: ....

**XYZ motion controller**
The LabEmbryoCam makes use of a CoreXY (https://en.wikipedia.org/wiki/CoreXY) style of motion control and this can be achieved using a range of different
microncontroller boards from both CNC and 3D printing suppliers. The Minitronics V2 board is used here because 
of a low cost and having integrated drivers (reducing setup complexity). More sophisticated boards would enable 
higher resolution (via microstepping) and quieter operation, but come at a higher cost.

Firmware and configuration files for the Minitronics board are accessible here: .....


**Raspberry Pi**
A Raspberry Pi (RPi) 4 8GB can run the LabEmbryoCam smoothly. A heatsink and fan are suggested for optimal performance, and a powered USB 
hub to prevent excessive power draw from the USB ports leading to unreliable hardware connections. The camera should be connected 
to the RPi using an HDMI-CSI adapter - to enable sufficient distance from the camera to the RPi, mounted on the 
rear of the instrument. Follow enclosed instructions for mounting both the heatsink and CSI-HDMI adapter to the Raspberry Pi.

The RPi can be flashed with the operating system image found here, containing all dependancies installed. This can then 
be loaded onto a microSD card using the Rasperry Pi Imager - https://www.raspberrypi.com/software/.

The lighting, manual input, and XYZ microcontrollers should all be attached to the RPi, via the USB hub, which is itself 
then connected to a USB port of the RPi. All that is left, is to connect a mouse, keyboard and a monitor. Note that the 
RPi uses a microHDMI, so an adapter (included in the bill of materials is attached).


Continue to..
:doc:`software`



