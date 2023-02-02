import cv2
import numpy as np
import skimage.util
import math
from scipy import signal
import multiprocessing as mp
from natsort import natsorted, ns
import contextlib
from tqdm import tqdm
import h5py
import os
from scipy import stats


# Utilities -----------------------------------------------------------

def frameCount(video):
    ''' Helper function for retrieving the frame count from a video. '''
    if not isinstance(video, cv2.VideoCapture):
        video = cv2.VideoCapture(video)
        release = True
    else:
        release = False

    frameCnt = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if release:
        video.release()

    return frameCnt

def frameRate(video):
    ''' Helper function for retrieving fps from a video. '''
    if not isinstance(video, cv2.VideoCapture):
        video = cv2.VideoCapture(video)
        release = True
    else:
        release = False

    fps = video.get(cv2.CAP_PROP_FPS)

    if release:
        video.release()

    return fps

def framesFromVideo(video):
    '''
    Grab frames from a video file.

    The supplied object can either be a filename or a VideoCapture
    object from opencv. Regardless, a generator will be created for
    grabbing frames from footage. 

    Keywords arguments:
        video    String or class.    Filename or opencv VideoCapture object to
                                     grab frames from (Required). 

    Returns:
        Generator for grabbing frames from the specified footage.

    '''
    if not isinstance(video, cv2.VideoCapture):
        video = cv2.VideoCapture(video)
        release = True
    else:
        release = False

    video.set(1, 0)
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        yield frame

    if release:
        video.release()

# Convenience function for various opencv versions
cvVers = int(cv2.__version__[0])
if cvVers == 4:
    def findContours(img):
        return cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
else:
    def findContours(img):
        _, contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        return contours, hierarchy

class EmptyPGbar:
    '''Dummy progress bar for progress bar context.'''
    @staticmethod
    def update(n):
        '''Dummy update for progress bar context.'''
        pass

@contextlib.contextmanager
def pgBar(total, show):
    '''
    Create a progress bar to be used in a 'with' context.

    Keyword arguments:
        total    Integer.    Length of progress bar (Required).
        show     Bool.       Whether to return a progress bar (Required).

    Returns:
        tqdm progress bar.

    '''

    if show:
        pgbar = tqdm(total=total)
        try:
            yield pgbar
        finally:
            pgbar.close()
    else:
        yield EmptyPGbar

def takeFirst(it):
    '''
    Retrieve a value from an iterable object.

    Keyword arguments:
        it    Iterable object (Required).

    Returns:
        First value from an iterable object.

    '''

    it = iter(it)
    try:
        return next(it)
    except StopIteration:
        return None

# HDF5 utils ----------------------------------
def slices(shape):
    ''' 
    Create a tuple of slices from a given shape.
    
    Keyword arguments:
        shape    Tuple.   Dimensions to creates slices (Required).

    Returns:
        Tuple.   Slices for the supplied dimension.

    '''
    return tuple(map(slice, shape))

class Dataset:
    ''' 
    Convenience wrapper around h5py. 

    Note all files hdf5 files are opened in 'a' mode via h5py.

    '''
    def __init__(self, filename):
        '''
        Keyword arguments:
            filename    String.    Filename to create HDF5 (Required).

        '''
        self.file = h5py.File(filename, mode='a')

    def close(self):
        ''' Closes the declared file. '''
        self.file.close()

    def keys_shapes(self):
        '''
        Convenience function for retrieving subdatasets and their corresponding
        dimensions from a HDF5 file.

        Keyword arguments:
            file    String.    File to grab metadata from (Required).

        Returns:
            Dict.    Dict of subdataset names and their corresponding dimensions.

        '''

        dims = {}
        for name in list(self.file.keys()): 
            dims[name] = self.file[name].shape
        return dims

    def empty(self, name, shape):
        '''
        Create an empty subdataset. 

        Keyword arguments:
            name    String.   Name for subdataset (Required).
            shape  Tuple.     Dimensions of new subdataset (Required).

        '''
        if name in list(self.file.keys()):
            del self.file[name]

        self.file.create_dataset(name, shape=shape)
        self.file.flush()

    def __getitem__(self, name):
        '''Getter for retrieving data from the declared file.'''
        return self.file[name]

    def __setitem__(self, name, data, shape=None):
        '''Setter that dumps data out-of-core to a given subdataset. '''
        if name not in list(self.file.keys()):
            self.file.create_dataset(name, data=data, shape=data.shape)
        else:
            if shape is None: shape = slices(data.shape)
            self.file[name][shape] = data
        self.file.flush()

@contextlib.contextmanager
def dataset(filename):
    '''
    Create a Dataset object for use in a 'with' context.

    Keyword arguments:
        filename    String.   Filename to create (Required).

    '''
    ds = Dataset(filename)
    try:
        yield ds
    finally:
        ds.close()

def exportResults(results, out_file):
    '''
    Export a results dict as a HDF5 file out-of-core.

    Keyword arguments:
        results    Dict.    Dict of results obtained from a data integration method (Required.
        out_file   String.  Filename to export results (Required).

    '''
    with dataset(out_file) as ds:
        for key in results: ds[key] = results[key]

def trimDatasets(in_files, keys_shapes, verbose=True):
    '''
    Trim a set of hdf5 files to a given set of subdataset shapes.

    Keyword arguments:
        in_files     List.   List of filenames to files to trim (Required).
        keys_shapes  Dict.   Dict of subdataset names with corresponding shapes
                             to trim to (Required).
        verbose      Bool.   Whether to print progress info, default is True.

    '''
    if verbose: print('EmbryoCV: Trimming datasets to uniform length...')
    with pgBar(total=len(in_files), show=verbose) as pgbar:
        for file in in_files:
            with dataset(file) as ds:
                for key in keys_shapes: 
                    ds[key] = ds[key][slices(keys_shapes[key])]
            pgbar.update(1)

def concatDatasets(in_files, out_file, cleanup=True, verbose=True):
    '''
    Combine a set of hdf5 files out-of-core.

    Note that in_files is sorted prior to concatenation.

    Keyword arguments:
        in_files     List.    List of filenames to files to combine (Required).
        out_file     String.  Filename to fill with the combined data (Required).
        cleanup      Bool.    Whether to remove the individual files, default is True.
        verbose      Bool.    Whether to print progress info, default is True.

    '''

    sortedFiles = natsorted(in_files, alg=ns.IGNORECASE)
    with dataset(takeFirst(sortedFiles)) as ds: dims = ds.keys_shapes()

    if verbose: print('EmbryoCV: Combining datasets into a single file...')
    with pgBar(total=len(in_files), show=verbose) as pgbar:
        with dataset(out_file) as DS:
            for key in dims: DS.empty(key, shape=(len(sortedFiles), *dims[key]))

            for i,file in enumerate(sortedFiles):
                with dataset(file) as ds:
                    for key in ds.keys_shapes():
                        DS[key][i,:] = ds[key][:]

                if cleanup:
                    os.remove(file)

                pgbar.update(1)

# Image analysis --------------------------------------------------------------------

def locateEmbryo(img):
    '''
    Locate the embryo in an image and return the bounding box dimensions.

    Note that this is quite a barebones method and may be somewhat inaccurate in images
    where an embryo is touching it's shell for example.

    Keyword arguments:
        img    Numpy.ndarray.   RGB image to process (Required).

    Returns:
        Numpy.ndarray.   Contour found for the embryo.

    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.medianBlur(thresh, 3)

    contours, hierarchy = findContours(mask)

    if contours:
        # Create mask for final contour detection
        areas = [cv2.contourArea(c) for c in contours]
        max_index = np.argmax(areas)
        embryoOut = contours[max_index]
        x,y,w,h = cv2.boundingRect(embryoOut)
        embryoRectMask = np.zeros(gray.shape, dtype='uint8')

        # bbox expanded for cases where some embryo has been excluded from the first mask
        cv2.rectangle(embryoRectMask, (x-10, y-10), (x+w+10, y+h+10), 255, -1) 
        onlyEmbryo = cv2.bitwise_and(gray, gray, mask=embryoRectMask)

        _, thresh2 = cv2.threshold(onlyEmbryo, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours2, hierarchy = findContours(thresh2)
        areas2 = [cv2.contourArea(c) for c in contours2]
        embryoOutline = contours2[np.argmax(areas2)]
    else:
        embryoOutline = None

    return embryoOutline

def contourStats(contour):
    '''
    Compute various stats for a given contour.

    Arguments:
    - contour:  Numpy.ndarray.  Array of coordinates describing the embryo contour.

    Returns:
    - Dict.     Dict of image statistics.

    '''

    def emptyStats():
        return dict(
            embryoOutline=np.nan,
            embryoArea=np.nan, 
            centroidsX=np.nan,
            centroidsY=np.nan,
            bbox=np.nan,
            aspect=np.nan,
            extent=np.nan,
            hullArea=np.nan,
            solidity=np.nan,
            minLength=np.nan,
            maxLength=np.nan,
            rotbbox=np.nan)

    if contour is None:
        stats = emptyStats()
    else:
        moments = cv2.moments(contour)

        if moments['m00'] == 0:
            stats = emptyStats()
        else:
            centroidX = int(moments['m10']/moments['m00'])
            centroidY = int(moments['m01']/moments['m00'])
            embryoArea = moments['m00']

            bbox = cv2.boundingRect(contour)
            x,y,w,h = bbox
            aspect = float(w)/h
            extent = embryoArea/(w*h)
            hull = cv2.convexHull(contour)
            hullArea = cv2.contourArea(hull)
            solidity = float(embryoArea)/hullArea
            rotbbox = cv2.minAreaRect(contour)

            stats = dict(
                embryoOutline=contour,
                embryoArea=embryoArea, 
                centroidsX=centroidX,
                centroidsY=centroidY,
                bbox=bbox,
                aspect=aspect,
                extent=extent,
                hullArea=hullArea,
                solidity=solidity,
                minLength=min(rotbbox[1]),
                maxLength=max(rotbbox[1]),
                rotbbox=rotbbox)

    return stats

# Taken from: https://stackoverflow.com/questions/11627362/how-to-straighten-a-rotated-rectangle-area-of-an-image-using-opencv-in-python/48553593#48553593
def get_sub_image(img, rect):
    center, size, theta = rect
    center, size = tuple(map(int, center)), tuple(map(int, size))
    M = cv2.getRotationMatrix2D( center, theta, 1)
    dst = cv2.warpAffine(img, M, img.shape[:2])
    out = cv2.getRectSubPix(dst, size, center)
    return out

def blockMean(img, contour):

    '''
    Find the blockwise means for an image at various resolutions.

    Note that the blockwise means are only calculated for the bounding box of the embryo. All other data 
    from the image is discarded. Resolutions calculated are 1x1, 2x2, 4x4, 8x8, 16x16.

    Keyword arguments:
        img      Numpy.ndarray.  Grayscale image (Required).
        contour  Numpy.ndarray.  Array of coordinates describing the embryo contour.

    Returns:
        Dict.   Dict of blockwise means, numbered according to their resolution.
                I.e. the keys correspond to block size, e.g. 'n8','n16' and so on.

    '''

    def crop(frame, blocksize):
        new_x, new_y = map(lambda v: math.floor(v/blocksize)*blocksize, frame.shape) 
        return frame[:new_x, :new_y]

    if contour is None:
        blockWiseMeans = dict(n1=np.nan)
        for i in range(2,16+2,2):
            blockWiseMeans['n{}'.format(i)] = np.full((i,i), np.nan)

        return blockWiseMeans

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    rot_rect = cv2.minAreaRect(contour)
    img = get_sub_image(img, rot_rect)
    cropped = crop(img, blocksize=16)

    x, y = cropped.shape

    blockWiseMeans = dict(n1=np.mean(cropped))
    ns = [2,4,8,16]
    for n in ns:
        block_shape = tuple(map(int, (x/n, y/n)))
        blocks = skimage.util.view_as_blocks(cropped, block_shape=block_shape)
        blockWiseMeans['n{}'.format(n)] = blocks.mean(axis=(2,3))

    return blockWiseMeans

def blockMeans(frames, lenFrames, verbose):

    '''
    Compute the blockwise means for video footage.

    Note that the blockwise means are only calculated for the bounding box of the embryo. All other data 
    from the image is discarded. Resolutions calculated are 1x1, 2x2, 4x4, 8x8, 16x16.

    Keywords arguments:
        frames       List.           List of rgb frames (Required).
        lenFrames    Integer.        Number of frames in video footage (Required).
        verbose      Boolean.        Whether to print progress info (Required).

    Returns:
        List of arrays for each resolution.

    '''

    if verbose: print('EmbryoCV: Computing image statistics...')

    with pgBar(total=lenFrames, show=verbose) as pgbar:
        blockMeans_1x1 = np.empty((lenFrames, 1))
        blockMeans_2x2 = np.empty((lenFrames, 2, 2))
        blockMeans_4x4 = np.empty((lenFrames, 4, 4))
        blockMeans_8x8 = np.empty((lenFrames, 8, 8))
        blockMeans_16x16 = np.empty((lenFrames, 16, 16))

        frameStats = []
        for i,frame in enumerate(frames):
            contour = locateEmbryo(frame)
            frameStats.append(contourStats(contour))
            _blockMeans = blockMean(frame, contour)
            blockMeans_1x1[i,:] = _blockMeans['n1']
            blockMeans_2x2[i,:,:] = _blockMeans['n2']
            blockMeans_4x4[i,:,:] = _blockMeans['n4']
            blockMeans_8x8[i,:,:] = _blockMeans['n8']
            blockMeans_16x16[i,:,:] = _blockMeans['n16']
            pgbar.update(1)

        return frameStats, [blockMeans_1x1, blockMeans_2x2, blockMeans_4x4, blockMeans_8x8, blockMeans_16x16] 

def signalWelch(blockWiseMeans, fps, verbose):

    '''

    Compute the frequency/power data for a set of images at various blockwise resolutions using
    welch's method.

    Keywords arguments:
        blockWiseMeans    List.     List of block-wise means for a video (Required).
        fps               Integer.  Frame-rate at which the footage was captured (Required).
        verbose           Boolean.  Whether to print progress information (Required).
        
    Returns:
    List.   List of arrays for the signal data at each resolution.

    '''

    if verbose: print('EmbryoCV: Computing power spectral data.')

    n1 = blockWiseMeans[0].flatten().tolist()
    signals_1x1 = signal.welch(
                        x=n1, 
                        fs=fps, 
                        scaling='spectrum', 
                        nfft=len(n1))

    signalData = [np.asarray(signals_1x1)]
    ns = [2,4,8,16]
    for i,n in enumerate(ns):
        arr = np.empty((n,n,2,len(signals_1x1[0])))

        for x in range(n):
            for y in range(n):
                arr[x,y,0,:], arr[x,y,1,:] = signal.welch(
                                                x=blockWiseMeans[i+1][:,x,y].flatten().tolist(), 
                                                fs=fps,
                                                scaling='spectrum', 
                                                nfft=len(n1))
        signalData.append(arr)

    return signalData

# Data analysis ----------------------------------------------------------------


def movementStats(centroidsX, centroidsY):

    '''
    Compute movement statistics for a sequence of centroids. 
    Arguments:
    - centroidsX: List. A sequence of x coordinates to the centroid of 
        an embryo in an image.
    - centroidsY: List. Same as above but for y coordinates.
    Returns:
    - List of distances between the nth centroid and nth-1 centroid.
    - List of mean, min, max and total distance between centroids.
    '''
    
    arr = np.array((centroidsX, centroidsY))

    if np.sum(np.isnan(centroidsX)) < 10:
        movement = np.linalg.norm(arr.T[:-1] - arr.T[1:], axis=1)
        meanDistance = np.nanmean(movement)
        minDistance = np.nanmin(movement)
        maxDistance = np.nanmax(movement)
        total = np.nansum(movement)
    else:
        meanDistance = np.nan
        minDistance = np.nan
        maxDistance = np.nan
        total = np.nan
        movement = np.full((1,len(centroidsX)-1), np.nan).flatten().tolist()

    return movement, [meanDistance, minDistance, maxDistance, total]

def lengthGrowthRegress(meanMinLengths, meanMaxLengths, minLengths, maxLengths):

    '''
    
    Compute the linear regression models for various length measurements.
    Arguments:
    - meanMinLengths: List. Sequence of means of minimum lengths, where there is a mean for
        each timepoint.
    - meanMaxLengths: List. Same as above, but for maximum lengths.
    - minLengths: List. Sequency of minimums for the minimum lengths at each timepoint.
    - maxLength: List. Same as above except for max of maximums.
    Returns:
    - List of models for each sequence type.
    '''

    x = list(range(1, len(minLengths)+1, 1))

    meanMinLM = stats.linregress(x=x, y=meanMinLengths) 
    meanMaxLM = stats.linregress(x=x, y=meanMaxLengths)
    minLM = stats.linregress(x=x, y=minLengths)
    maxLM = stats.linregress(x=x, y=maxLengths)

    return [meanMinLM, meanMaxLM, minLM, maxLM]

def areaGrowthRegress(meanAreas, minAreas, maxAreas):

    '''
    
    Compute the linear regression models for various area measurements.
    Arguments:
    - meanAreas. List. Sequence of means of embryo area, where there is a mean for each 
        timepoint.
    - minAreas. List. Same as above except for minimums.
    - maxAreas. List. Same as above except for maximums.
    Returns:
    - List of models for each sequence type.
    '''

    x = list(range(1, len(meanAreas)+1, 1))

    meanLM = stats.linregress(x=x, y=np.log(meanAreas))
    minLM = stats.linregress(x=x, y=np.log(minAreas))
    maxLM = stats.linregress(x=x, y=np.log(maxAreas))

    return [meanLM, minLM, maxLM]

# Data integration ----------------------------------------------------------------------

def packResults(frameStats, blockWiseMeans, signalData, verbose):

    emOutlines = [stats['embryoOutline'] for stats in frameStats]

    emOutlineArr = np.full((len(frameStats), 2, 5000), np.nan)
    outlineLengths = []
    for i,arr in enumerate(emOutlines):
        if isinstance(arr, np.ndarray):
            length = arr.shape[0]
            outlineLengths.append(length)
            emOutlineArr[i,:,0:length] = np.swapaxes(arr[:,0,:],0,1)
        else:
            emOutlineArr[i,:,:] = np.nan

    centroidsX, centroidsY = zip(*[(stats['centroidsX'], stats['centroidsY']) for stats in frameStats])
    movement, movement_stats = movementStats(centroidsX, centroidsY)

    # Packing data into dict ------------------------
    if verbose: print('EmbryoCV: Packing results...')

    embryoArea = [stats['embryoArea'] for stats in frameStats]
    bbox = [stats['bbox'] for stats in frameStats]
    aspect = [stats['aspect'] for stats in frameStats]
    extent = [stats['extent'] for stats in frameStats]
    hullArea = [stats['hullArea'] for stats in frameStats]
    solidity = [stats['solidity'] for stats in frameStats]
    minLength = [stats['minLength'] for stats in frameStats]
    maxLength = [stats['maxLength'] for stats in frameStats]
    rotbbox = [stats['rotbbox'] for stats in frameStats]

    bboxArr = np.asarray(bbox)
    rotbboxArr = [(x,y,w,h,a) for (x,y),(w,h),a in rotbbox]
    rotbboxArr = np.asarray(rotbboxArr)

    area_stats = np.empty(4)
    area_stats[0] = np.nanmean(embryoArea)
    area_stats[1] = np.nanmin(embryoArea)
    area_stats[2] = np.nanmax(embryoArea)
    area_stats[3] = np.nansum(embryoArea)

    length_stats = np.empty(5)
    length_stats[0] = np.nanmean(minLength)
    length_stats[1] = np.nanmean(maxLength)
    length_stats[2] = np.nanmin(minLength)
    length_stats[3] = np.nanmax(maxLength)
    length_stats[4] = np.nansum(maxLength)

    image_stats = np.empty((len(frameStats), 5))
    image_stats[:,0] = aspect
    image_stats[:,1] = extent
    image_stats[:,2] = hullArea
    image_stats[:,3] = centroidsX
    image_stats[:,4] = centroidsY

    dataset = dict(
                Area=np.asarray(embryoArea),
                Length=np.asarray(maxLength),
                Movement=np.asarray(movement),
                EmbryoOutline=emOutlineArr,
                Solidity=np.asarray(solidity),
                AreaSummaryStats=area_stats,
                LengthSummaryStats=length_stats,
                MovementSummaryStats=np.asarray(movement_stats),
                AncillaryImageStats=image_stats,
                BoundingBox=bboxArr,
                RotatedBoundingBox=rotbboxArr,
                BlockWise_1x1=blockWiseMeans[0],
                BlockWise_2x2=blockWiseMeans[1],
                BlockWise_4x4=blockWiseMeans[2],
                BlockWise_8x8=blockWiseMeans[3],
                BlockWise_16x16=blockWiseMeans[4],
                FreqOutput_1x1=signalData[0],
                FreqOutput_2x2=signalData[1],
                FreqOutput_4x4=signalData[2],
                FreqOutput_8x8=signalData[3],
                FreqOutput_16x16=signalData[4])

    return dataset, np.nanmax(outlineLengths)

def model(dataset):
    length_stats = dataset['LengthSummaryStats']
    lengthModels = lengthGrowthRegress(
        meanMinLengths=length_stats[:,0],
        meanMaxLengths=length_stats[:,1],
        minLengths=length_stats[:,2],
        maxLengths=length_stats[:,3])

    length_models = np.empty((4, len(lengthModels[0])))
    length_models[:,:] = lengthModels

    area_stats = dataset['AreaSummaryStats']
    areaModels = areaGrowthRegress(
        meanAreas=area_stats[:,0],
        minAreas=area_stats[:,1],
        maxAreas=area_stats[:,2])

    area_models = np.zeros((3, len(areaModels[0])))
    area_models[:,:] = areaModels

    dataset['LengthGrowthLM'] = length_models
    dataset['AreaGrowthLM'] = area_models

    return dataset

# # Test

# import re

# def embryocv_compute(file, outpath=None, verbose=False):
#     ''' Convenience function for processing callback below. '''
#     lenFrames = frameCount(file)
#     fps = frameRate(file)

#     frameStats, blockWiseMeans = blockMeans(framesFromVideo(file), lenFrames, verbose)
#     signalData = signalWelch(blockWiseMeans, fps, verbose)

#     results, mxLength = packResults(frameStats, blockWiseMeans, signalData, verbose)
    
#     if outpath is None: outpath = re.sub('.avi', '.h5', file)
#     exportResults(results, outpath)
    
#     return outpath

# out = embryocv_compute('/home/z/Documents/radix_raw/last/25C_E8_7d.avi', verbose=True)

# with dataset(out) as d:
#     print(d.keys_shapes())