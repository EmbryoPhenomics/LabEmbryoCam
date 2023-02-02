Frame Spacers, Linear Rails and Front corners
========


.. list-table::
   :widths: 4 2 3 5
   :header-rows: 1

   * - Part
     - Number
     - Details
     - Location
   * - **3D printed parts**
     -
     -
     -
   * - front_corner_left_top.stl
     - 1
     - Front top corner part
     - Front corner
   * - front_corner_right_top.stl
     - 1
     - Front top corner part
     - Front corner
   * - front_corner_left_bottom.stl
     - 1
     - Front corner bottom part
     - Front corner
   * - front_corner_right_bottom.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - front_left_bottom_small.stl
     - 1
     - Front corner bottom small
     - Front corner   
   * - spacers_back_mid(2).stl
     - 2
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_back_left.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_back_right.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_side_back_left.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_side_back_right.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_side_front_right.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_bottom_side.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_front_bottom_left.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_front_bottom_right.stl
     - 1
     - Front corner bottom part
     - Front corner  
   * - spacers_mid_and_top_bracket_anti(4).stl
     - 4
     - Front corner bottom part
     - Front corner    
   * - spacers_mid_and_top_bracket(4).stl
     - 4
     - Front corner bottom part
     - Front corner    
   * - spacers_top_back_left.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - spacers_top_back_right.stl
     - 1
     - Front corner bottom part
     - Front corner    
   * - **Parts**
     -
     -
     -
   * - linear rails
     - 2
     - y-axis
     -
   * - **Fixings**
     - 
     - 
     -
   * - F623ZZ flanged bearings
     - 12
     - 
     -  flanged
   * - M3 washers
     - 18
     - 
     - 
   * - M3 Sockethead 35 mm
     - 14
     - 
     - 
   * - M3 nuts
     - 6
     - 
     -
   * - 

Aluminium extrusion
---------------
Before proceeding with assembling the instrument, it is easiest to loosely attach the two y-axis linear rails with XX mm countersunk bolts and slide nuts. 
Tighten just enough to stop them falling off when you turn the extrusion upside down. These rails are what will enable the 'carriage' to slide back and forth.
Attach one linear rail to each of XXX mm 2040 pieces of aluminium extrusion. 

Now, insert M.. bolts and slide nuts through the holes of all of the 3D printed spacer parts before attempting to fit them. Make sure to push the bolts all the way through the 3D printed part
and ensure it turns freely before proceeding. Screw the slide nut onto the bolt, but only one turn. Note that the spacers should have the smooth part facing outwards, and that there
are different sizes for different positions on the instrument.

Ensure the two pieces of extrusion with linear rails attached are attached front-to back on the layer above the bottom-most layer. If in doubt, check the CAD model.
When installing these pieces of extrusion, the linear rail should be on the side of the extrusion closest to the centre of the instrument. 

Start assembling from the bottom-up. First insert the spacers that will sit on the previously assembled bottom square. Line up the slide nuts in these 3D printed parts 
with the groove of the extrusion and insert them, before tightening. Note when tightening that the part should be pulled towards the extrusion - i.e. the two are bound
together attached. If this does not happen, try untightening the slide nut and repeating the process. 

.. raw:: html

    <iframe src="https://plymouth222.autodesk360.com/shares/public/SH35dfcQT936092f0e437cf5bbca7ac59d0d?mode=embed" width="640" height="480" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>




Front motion corners
---------------
The front corners are one of the more complex parts of building the LabEmbryoCam. The left and right sides are not symmetrical and are responsible
for mounting the X and Y stepper motors, and four pulleys around which the toothed belts, used for transmitting the motion, are routed.

Begin by inserting the .. bolts through the left and right lower parts, ensuring they rotate freely and then loosely attaching the slidenuts.
First, focus on the left slide of the LabEmbryoCam, and attach the lower part in the left front coner as shown below. The intersecting 
extrusion are transparent in these images to help see how the 3D printed front corner part attaches.

.. list-table:: 
    * - .. figure:: ../_build/html/_images/front_corner_right.png

           Right corner

      - .. figure:: ../_build/html/_images/front_corner_left.png

           Left corner


Repeat the process with the lower part of the right front corner. Once attached, both of the lower front corner parts should be flush with the top 
of the extrusions to which they are attached.

The LabEmbryoCam makes use of some 'home-made' pulleys, using 3 x M3 washers interleaved between 2 x F623ZZ
flanged bearings, as shown below. The belts run over the flanged bearings - so ensure the flanges are on the outer 
edge to guide the belt (as seen below).

.. figure:: ../_build/html/_images/pulley.png
  :width: 250

Each front corner, will incorporate two of these pulleys, and these are central to the XY motion of the instrument. At this stage, begin 
to attach the screws (note the lengths and types from the CAD model below) to the front corners responsible for mounting the stepper 
motors and pulleys. 
.. list-table:: 

    * - .. figure:: ../_build/html/_images/front-left-corner.png

           Left corner

      - .. figure:: ../_build/html/_images/front-right-corner.png

           Right corner


See below for an interactive CAD window to see their locations, including the four long .. mm bolts for
the stepper motions. Note that the mounting orientation for the stepper motor does not really matter, but having 
the cable attachments facing towards the front of the instrument makes routing cables tidier.

.. raw:: html

  <iframe src="https://plymouth222.autodesk360.com/shares/public/SH35dfcQT936092f0e43dc4b1c1085026d80?mode=embed" width="640" height="480" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

The top and bottom 3D printed pieces for each corner fit together, but should be very snug so will require pressure to fit together. Consult the CAD 
above if unsure about how these parts fit together.


