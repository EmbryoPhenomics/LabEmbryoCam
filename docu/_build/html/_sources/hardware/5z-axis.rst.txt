Z-axis
==============

**Parts Required**

+----------------------------------------------+--+---------------+
|﻿                                             |N |Location       |
+==============================================+==+===============+
|**Parts**                                     |  |               |
+----------------------------------------------+--+---------------+
|Z stepper motor - 21 oz                       |1 |z-carriage     |
+----------------------------------------------+--+---------------+
|Flexible motor coupling for Z axis            |1 |z-carriage     |
+----------------------------------------------+--+---------------+
|Bearing mount for Z-axis smooth rod           |1 |z-carriage     |
+----------------------------------------------+--+---------------+
|Leadscrew(8mm) for Z-axis (85 mm needed)      |1 |z-carriage     |
+----------------------------------------------+--+---------------+
|Leadscrew(8mm) nut for carriage               |1 |z-carriage     |
+----------------------------------------------+--+---------------+
|Smooth steel rod (2 x 128, 2 x 106) mm needed)|1 |z-carriage     |
+----------------------------------------------+--+---------------+
|3mm Cable ties                                |4 |z-carriage     |
+----------------------------------------------+--+---------------+
|F623ZZ                                        |8 |Y-axis         |
+----------------------------------------------+--+---------------+
|Linear bearing                                |4 |Z-axis         |
+----------------------------------------------+--+---------------+
|Raspberry Pi HQ camera                        |1 |camera carriage|
+----------------------------------------------+--+---------------+
|Pimorini microscope lens                      |1 |camera carriage|
+----------------------------------------------+--+---------------+
|LED 2 inch light                              |1 |camera carriage|
+----------------------------------------------+--+---------------+
|**3D prints**                                 |  |               |
+----------------------------------------------+--+---------------+
|y_mount_big_l.stl                             |  |               |
+----------------------------------------------+--+---------------+
|y_mount_big_r.stl                             |  |               |
+----------------------------------------------+--+---------------+
|y_mount_small_l.stl                           |  |               |
+----------------------------------------------+--+---------------+
|y_mount_small_r.stl                           |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_camera_mount.stl          |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_camera_tripod_adapter.stl |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_light_bolt_0.97.stl       |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_light_insert.stl          |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_limit_trigger.stl         |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_optics_insert.stl         |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly_rod_screw(4).stl          |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_assembly.stl                       |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_light_carrier.stl                  |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_light_screw.stl                    |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_light_slider.stl                   |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_optics_screw.stl                   |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_rail_mount_insert.stl              |  |               |
+----------------------------------------------+--+---------------+
|z_carriage_rail_mount.stl                     |  |               |
+----------------------------------------------+--+---------------+


X-axis
---------------
The x-axis assembly consists of attaching the piece of 2020 extrusion that carries the carriage containing the optics etc.

Begin, by attaching the y_mount_big_l and y_mount_big_r 3D printed parts to the linear rail carriages (these should be hanging from the linear rails underneath the 2040 extrusion running backwards and forwards on the instrument. Once these parts are attached, the xx mm pieces of 2020 extrusion should sit comfortably on these pieces, and can be attached using bolts and slide nuts, as seen in the CAD window below.

.. raw:: html

    <iframe src="https://plymouth222.autodesk360.com/shares/public/SH35dfcQT936092f0e438b9ebf83b76d6778?mode=embed" width="640" height="480" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

`X-axis`

Each x-axis end piece (y_mount_big_l and y_mount_big_r) incorporates four pulleys, as used in the front corners. Check the CAD model to see the location of these and insert the appropriately sized screws. Once the pulleys are in place, attach the top pieces of the x-axis ends (y_mount_small_l and y_mount_small_r) and complete the assembly of this section by attaching the appropriate fixings.

Z-axis
---------------
The z-axis allows a stepper motor to move the camera, lens and lighting up and down. Investigate this CAD model to see how the z-axis will look once fully assembled. Tighten the leadscrew nut onto the carriage assembly and the coupling onto the light assembly.

The z-axis assembly consists of a carriage holding a z-axis assembly that moves the camera and light up and down.

.. raw:: html

    <iframe src="https://plymouth222.autodesk360.com/shares/public/SH35dfcQT936092f0e43e46b0bd27f053184?mode=embed" width="640" height="480" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

`Z-axis assembly`


Begin assembly of the z-carriage by attaching the z-carriage as seen below, to the linear rail carriage.

.. raw:: html

    <iframe src="https://plymouth222.autodesk360.com/shares/public/SH35dfcQT936092f0e43d4b398cfbf04c0a4?mode=embed" width="640" height="480" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

`Z-axis carriage`

Before attaching the z-axis carriage to the linear rail carriage put cable ties for holding the linear bearings through the carriage part. This is harder to do once the linear rail and carriage are attached.


.. figure::../_static/z_carriage_fixings.png
  :width: 700

`Z-axis carriage fixings`



Now, begin assembling the x-axis assembly. The sequence of assembly is important.

1. Slide the 126 mm smooth rods to the front of the z-assembly and insert the linear bearings onto each rod
   (Fig. 1. below)

2. Attach the z-axis slimmer stepper motor to the back of the z-axis assembly (Fig. 2. below). 
   
3. Attach the optics rail to the front of the z-axis assembly (Fig. 3 below).
   
4. The two 108 mm rods can now be inserted into the back of the carriage, with a linear bearing on each, but 
   this must be done with the assembly attached to the linear rail (Fig. 4 below).  

.. list-table:: 

    * - .. figure:: ../_static/front-rods.png

           1.Front rods

      - .. figure:: ../static/z-stepper.png

           2.Z-stepper motor

    * - .. figure:: ../_static/optics-slider.png

           3.Optics slider
   
      - .. figure:: ../_static/z-axis.png

           4.Rear rods and z-limit switch

To get the carriage assembly square - with the rods fully inserted into the top of the carriage assembly, pressure 
is required. Here, a clamp is helpful.

Once the four rails are inserted into the four linear bearings, add the flexible coupling to the stepper motor shaft.
Note: that the coupler should have a thick and thin end. Put the thin end onto the stepper motor shaft, and then 
thread the leadscrew down from above through the two leadscrew nut and coupler (in the light assemblies and z-carriage) -
see CAD window at top of page if unsure.

5. Finally, attach the LED ring light to the light assembly. Before doing so, four wires will need to be soldered
onto the LED ring, and should be long enough to reach the microcontroller at the back of the instrument (approx. 60 cm).

Continue to :doc:`3frame2`




