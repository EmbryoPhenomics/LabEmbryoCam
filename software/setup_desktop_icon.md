# To set up desktop icon:

Create the following `lec.desktop` file:

```
[Desktop Entry]
Name=LabEmbryoCam App
Version=v1.0
Icon=/path/to/icon
Exec=python /path/to/app_folder/app.py
Path=/path/to/app_folder
Terminal=true
Type=Application
```

And complete it with the required parameters. 

Next you need to call the following command in the terminal:

`sudo desktop-file-install lec.desktop`

to install the Desktop Icon.

It should now be visible in the system tray. 