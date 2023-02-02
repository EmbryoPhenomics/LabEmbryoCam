# LabEP software

### Important note - hardware layout for steppers and limit switches!

- X and Y limit switches plug into corresponding slots on minitronics board
- Right stepper motor plugs into X axis driver on minitronics board
- Left stepper motor plugs into Y axis driver on minitronics board


### To do

- Table interactivity - **done**
- Button XYZ docs - **not needed**
- Scripts for interacting with video and analysing them
- Docs for user guide 
- Move limit switches
- Multiprocessing for npy to avi conversion



## Table changes 

- Retrieve current position, add into table like in MM?
- Remove can be added in-line
- Add can be added directly with current position retrieval
- Update can be changed to replace but 

#### Debug/Develop

- [ ] Email notifications
	- Needs to change to different system because gmail has removed access from some third party apps
	- **Not needed because of remote access?**

- [x] Memory buffer for improving capture performance
- [x] Checks for serial ports to enable 
- [x] Lossless footage capture
- [x] Config files for entire 
	- Camera settings
	- XY coordinates and embryo labels
- [x] Metadata for experiment data
	- Camera settings
	- Position lists
	- Datetimes for acquisitions?
- [x] Live acquisition info
	- Timepoint which it's on
	- Current replicate
- [ ] AppImage? Or Python executable, using PyInstaller?
- [x] Interrupt/Stop acquisition feature 


#### Test/Benchmark

- [ ] XYZ positions (returns to same positions?)
- [ ] Coordinate space for multiwell plates
- [ ] Many repeated acquisitions/experiments
- [x] Live acquisition info

#### Refactor

- [ ] Remove implementations for other platforms




## XYZ accuracy

- Used 0.5x0.5mm2 - 5x5mm2 grid for comparison
	- Coordinates list for different distances
		- 4-6 units moved is accurate in y axis
		- <=2 units moved is not accurate in y axis
			- Approx 0.5 units out each time
		
- 0.5 mm -> 90 px
- 0.5 mm -> 0.25 in coordinate space
- 