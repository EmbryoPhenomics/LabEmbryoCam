import threading
from multiprocessing import Process

class Camera:
    '''
    Camera integration layer

    This class integrates all platform specific camera modules to provide
    a platform agnostic API for interacting with different cameras.

    Parameters
    ----------
    platform : str
        Name of desired platform (options currently are: 'opencv', 'picamera' and 'vimba')
    benchmark : bool
        Whether to benchmark acquisitions, streams etc. Default is True.

    Returns
    -------
    camera : Camera
        Instance of camera layer.

    Raises
    ------
    ValueError
        If the supplied platform string is not recognised.

    '''
    def __init__(self, benchmark=True):
        self.benchmark = benchmark
        self.platform = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def startup(self, platform):
        if platform == 'opencv':
            from camera_backend_opencv import OpenCV

            self.platform = OpenCV(benchmark=self.benchmark)

        elif platform == 'picamera':
            from camera_backend_pi import PiCam

            self.platform = PiCam(benchmark=self.benchmark)

        elif platform == 'picamera2':
            from camera_backend_picamera2 import PiCam2

            self.platform = PiCam2(benchmark=self.benchmark)

        elif platform == 'vimba':
            from camera_backend_vimba import Vmb

            self.platform = Vmb(benchmark=self.benchmark)

        elif platform == 'opencv-gst':
            from camera_backend_opencv_gst import OpenCV_GST        

            self.platform = OpenCV_GST(benchmark=self.benchmark)
            tmp = self.platform.grab()
            print(str(tmp.shape))

        else:
            raise ValueError(f'{platform} provided not recognised. Currently supported platforms are opencv, opencv-gst, picamera and vimba.')

    def get(self, name):
        '''
        Retrieve the current value for a given camera setting.

        Parameters
        ----------
        name : str
            Name of setting to retrieve.

        Returns
        -------
        value : int or float or str
            Current value for a given setting.

        '''
        return self.platform.get(name)

    def set(self, name, value):
        '''
        Set the value for a given setting.

        Parameters
        ----------
        name : str
            Name of setting to set.
        value : int or float or str
            Value to set setting to.

        Notes
        -----
        For cameras using vimba, only numeric settings are currently supported.

        '''
        self.platform.set(name, value)

    def grab(self):
        '''
        Retrieve a single frame.

        Returns
        -------
        frame : ndarray
            Still image.

        '''
        print('cam layer triggered')
        return self.platform.grab()

    def stream(self, separate_thread=False):
        '''
        Live stream footage from the specified camera.

        Notes
        -----
        Regardless of platform, opencv is used to display images live.

        '''
        if separate_thread:
            thread = threading.Thread(target=self.platform.stream)
            thread.start()
        else:
            self.platform.stream()


    def acquire(self, path, time, in_memory):
        '''
        Acquire footage and export to disk.

        Parameters
        ----------
        path : str
            Filename to save footage to on disk. 
        time : int or float
            Time to acquire footage for. 

        Notes
        -----
        Because opencv is used for exporting footage to disk, only file types 
        accepted by the ``VideoWriter`` class will work (e.g. '.avi' or '.mp4')

        Examples
        --------
        Here is a simple example for acquiring 10 seconds of footage at the default 
        settings from a webcam using opencv:

        >>> with Camera('opencv') as cam:
        ...     cam.acquire('./video.avi', 10)

        '''
        self.platform.acquire(path, time, in_memory)
        self.acq_data = self.platform.benchmarker.data

    def close(self):
        '''
        Perform teardown of the specified camera instance.
    
        '''
        if self.platform is not None:
            self.platform.close()


