# Guide for creating a new disk image

Download a raspbian lite image from the official website (https://www.raspberrypi.com/software/operating-systems/), latest version compatible with the LEC software is 32 or 64 bit BullsEye. 

Once you have flashed an SD card with a rapsbian lite image and completed the initial setup on a raspberry pi, follow the steps outlined here: https://github.com/TheMaroonHatHacker/gnomeforpi. This will set up Gnome on the raspbian OS, providing us a Gnome desktop environment and a virtual keyboard for use with the touchscreen that comes each LEC system. To enable the virtual keyboard, simply navigate to the accessibility settings and enable virtual keyboard.

Next, you can download the LEC software via the current GitHub repository, and subsequently you can install the required dependencies for the LEC software via `pip3 install -r requirements.txt`. Once this step has completed the image should be fully set up. 

To set up the desktop icon, please see `setup_desktop_icon.md` in this repository.