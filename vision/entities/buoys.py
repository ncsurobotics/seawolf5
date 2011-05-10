
from __future__ import division
import math
import ctypes

import cv

from entities.base import VisionEntity
import libvision

BUOY_GREEN = 0
BUOY_RED = 1
BUOY_YELLOW = 2

# Tuning Values
FILTER_TYPE = cv.CV_GAUSSIAN
FILTER_SIZE = 11
MIN_BLOB_SIZE = 200

class BuoysEntity(VisionEntity):

    name = "BuoysEntity"
    camera_name = "forward"

    def __init__(self, color_of_interest=BUOY_RED):
        self.color_of_interest = color_of_interest

    def initialize_non_pickleable(self, debug=True):

        if debug:
            cv.NamedWindow("Hist")

    def find(self, frame, debug=True):

        blobs = find_blobs(frame, debug)

        # Filter blobs
        #TODO

        # Track blobs
        #TODO

        if debug:

            # Draw blobs and centers
            for blob in blobs:
                cv.Rectangle(frame, (blob.left, blob.top), (blob.right, blob.bottom), (0,0,255))
                #cv.Circle(frame, (int(blob.cent_x),int(blob.cent_y)), 3, (0,0,255))

        return len(blobs) > 0

    def __repr__(self):
        return "<BuoysEntity>"


def find_blobs(frame, debug=True):
    '''Find blobs in an image.

    Hopefully this gets blobs that correspond with
    buoys, but any intelligent checking is done outside of this function.

    How it works
    ------------
    This function sums the laplacian of gaussian of some of the channels that
    should distinguish the buoys best.  The total laplacian is then scaled from
    0-255 and an otsu threshold is performed.  A blob detection is then
    performed on the resulting binary image.

    '''

    # Filter
    filtered = cv.CreateImage(cv.GetSize(frame), 8, 3)
    cv.Smooth(frame, filtered, FILTER_TYPE, FILTER_SIZE, FILTER_SIZE)

    # Grab hue, saturation, red and green channels
    #TODO: Possibly not all of these channels are needed
    filtered_hsv = cv.CreateImage(cv.GetSize(filtered), 8, 3)
    cv.CvtColor(filtered, filtered_hsv, cv.CV_BGR2HSV)
    channels = [libvision.misc.get_channel(filtered_hsv, i) for i in xrange(2)]+\
        [libvision.misc.get_channel(filtered, i) for i in xrange(1,3)]

    # Sum the laplacian from each channel
    total_laplace = cv.CreateImage((filtered.width,filtered.height), cv.IPL_DEPTH_32F, 1)
    cv.SetZero(total_laplace)
    for i, channel in enumerate(channels):
        channel_laplace = cv.CreateImage((channel.width,channel.height), cv.IPL_DEPTH_32F, 1)
        #cv.Sobel(channel, channel_laplace, 1, 1, 11)
        cv.Laplace(channel, channel_laplace, 19)
        cv.AbsDiffS(channel_laplace, channel_laplace, 0)
        cv.Add(channel_laplace, total_laplace, total_laplace)

    # Scale total_laplace 0-255 and store in result
    result = cv.CreateImage((channel.width,channel.height), 8, 1)
    cv.SetZero(result)
    max_value = cv.MinMaxLoc(total_laplace)[1]
    cv.ConvertScaleAbs(total_laplace, result, 255/max_value)

    # Get otsu threshold of total_laplace
    hist = cv.CreateHist([256], cv.CV_HIST_ARRAY, [[0,255]], 1)
    cv.CalcHist([result], hist)
    threshold = libvision.filters.otsu_get_threshold(result)
    max_value = int(cv.GetMinMaxHistValue(hist)[1])

    # Show histogram
    if debug:
        hist_image = libvision.hist.histogram_image(hist, color=(0,255,0))
        cv.Line(hist_image, (threshold,0), (threshold,255), (255,255,255))
        cv.ShowImage("Hist", hist_image)

    # Threshold
    cv.Threshold(result, result, threshold, max_value, cv.CV_THRESH_BINARY)
    # There will be a giant spike on the very left of the histogram if we
    # see something, because max_value will be much greater than most
    # pixels.  If there isn't a large enough spike, ignore the image.
    # The reason for this becomes more clear if you study the histogram on
    # test footage.
    if cv.QueryHistValue_1D(hist, threshold)/max_value >= 0.01:
        return []

    # Get blobs
    blobs_p = libvision.cmodules.BlobStruct_p()
    num_blobs = libvision.cmodules.blob.find_blobs(result, ctypes.pointer(blobs_p), 10, MIN_BLOB_SIZE)
    # The blobs are coppied here because we want to free the memory allocated
    # for them in C.  In the future libvision should do this for us.
    blobs = []
    for i in xrange(num_blobs):
        blob = libvision.cmodules.BlobStruct()
        ctypes.pointer(blob)[0] = blobs_p[i]
        blobs.append(blob)
    libvision.cmodules.blob.blob_free(blobs_p, num_blobs)

    return blobs