# LabEmbryoCam software 

Software for controlling and interfacing the with LabEmbryoCam instrument, with built-in front-end web application and backend modules/drivers for controlling associated hardware and conducting image acquisitions. 

## Change log from v1.0 - v1.1

- Removal of deprecated ui components:
	- Connect camera button (camera driver initiated on startup of app)
	- Inputs and button for email progress updates (automatically enabled if details provided in config file)
- Collapse of app layout to single page, thus removing previous tab layout
- Restructure of layout to distinct sections for ease of use/readability
- Addition of pop-ups for notifying users when camera live stream has been left running and/or when video save path already exists 
- Disable all ui components when start acquisition button has been clicked

