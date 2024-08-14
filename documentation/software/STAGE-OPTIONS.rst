**STAGE-OPTIONS**
==============

.. image:: ../_build/html/_images/homing.png

# 3. XYZ CONTROLS AND SETTINGS

-----------------

The first step required in setting up any experiment with the LEC is to home, or 'Set Origin' of the XYZ stage. This is essential to ensure that the correct origin is used when finding and creating positions and without doing this the XYZ stage will not be responsive. 

To home the stage, click the `Set Origin` button in the user interface.

***Before homing the stage, make sure there are no objects that could obstruct the movement of the stage - such as the lens being too high. Also, make sure not to use the app whilst the stage is homing as this could interfere with the process.***




-----------------

# 5. USING MANUAL CONTROLS TO FIND AND SAVE POSITIONS

-----------------

The manual controls can be used once the stage has finished homing. These can be found in **XYZ controls and settings**:

.. figure:: ../_static/xyz-ctrl.png
  :width: 450
  
The four buttons determine the step size of the movements of the XYZ stage - from 10mm to 0.01mm. Large movements are more easily achieved with a 10 mm step size, whereas smaller movements require a smaller step size. The stage will complete one 'step' for each press of the relevant button.

In conjunction with the camera live video stream, move the stage using the manual controls to move the camera to a desired position. Once you have a position that you want, click the `Current` button in the xyz section to record the current position:

.. figure:: ../_static/expt-progress.png
  :width: 450
  
This will add a position entry into the position list. Note that all columns and rows in the table are editable - so you can give the position a name/label.

You can repeat this step until you have recorded all the positions you want. Once you have completed recording positions, the next step is to enter the parameters for the acquisition before starting the experiment. 

The following are descriptions for each of the controls and components in the XYZ controls and settings section of the user interface:

* **Set Origin**: Press this button to home the stage at startup of the user interface
* **Left group of arrows**: These arrows correspond to moving the stage in the X and Y axis, you can move the stage forward (down arrow), backward (up arrow), left and right, but also diagonally.
* **Right group of arrows**: These arrows move the stage up and down in the Z axis.

The **XYZ View** section will populate with the relative positions of the XYZ positions that you record. If you click the toggle switch **Activate graph** this will mean that positions clicked on in this window will move the stage to that position. This is an effective way of quickly reviewing and adjusting positions.

* **Activate graph**: Enabling this switch will allow you to click on positions on the graph and then the stage will move to the select position. This can be an easy way to double-check all your positions are correct whilst you have a live stream open.

Additionally, the other settings in the **XYZ View** are:

* **Dimension**: Enabling this switch can switch between 2D or 3D view in the position plot, 3D view can be useful for visualising the z axis positions (i.e. seeing the relative heights of different positions).
* **Generate XY**: This enables the automatic creation of the entirety of a multiwell plate's positions. This is deactivated, unless you first create a position (using the **XYZ Positions** section - see below) labelled A1 (corresponding to the top left corner of a multiwell plate. Once this is done, the **Generate XY** will use this position as the basis to create X and Y coordinates for all subsequent wells. 24, 48, 96 and 384 well plates are included.

The **XYZ Positions** section enables creation of X, Y and Z position lists:

* **Current**: Press this button to retrieve the coordinates of the current position where the stage is at. A new entry will be added into the position list below where it can be edited further.
* **Replace**: Press this button to replace the coordinates of the selected position with those at the current position of the stage. This can be used to update a position if an animal has moved or gone out of focus. **Note that you must select a position in the position list table via clicking on the circle icon in the second column of the position list for the position you’d like to replace.**
* **Position list table**: Position list where coordinates are recorded. The first column is for removing position entries from the list, simply click the x icon for the position you’d like to remove. The second column is to permit selection of specific position entries for updating their coordinates. Finally, columns X, Y, Z and Label are all editable similar to an excel spreadsheet.








