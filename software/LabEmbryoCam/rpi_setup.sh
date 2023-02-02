wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
sudo apt-get update
sudo apt-get install build-essential cmake pkg-config libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 python3-dev -y
pip install opencv-contrib-python==4.1.0.25

pip install dash==1.9.1
#pip install pandas - slow
sudo apt-get install python3-pandas
pip install tqdm
pip install natsort
pip install dash-daq
#pip install scikit-image
sudo apt-get install skimage
pip install h5py

#pip install werkzeug==2.0.0
#pip install dash==1.9.1
