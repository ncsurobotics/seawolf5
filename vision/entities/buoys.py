
from __future__ import division
import math
import ctypes
from collections import namedtuple

import cv

from entities.base import VisionEntity
import libvision

Point = namedtuple("Point", ["x", "y"])

BUOY_GREEN = 0
BUOY_RED = 1
BUOY_YELLOW = 2

############################### Tuning Values ###############################
#FILTER_TYPE = cv.CV_GAUSSIAN
FILTER_TYPE = cv.CV_GAUSSIAN
FILTER_SIZE = 11
# If we want to see buoys from far away, 50 is a good value for MIN_BLOB_SIZE.
# However, if we align with the path first, the buoys will be much closer, and
# this can be raised to 200.
MIN_BLOB_SIZE = 100
TRACKING_MIN_Z_SCORE = 10
TRACKING_ALPHA = 0.6
TRACKING_TEMPLATE_MULTIPLIER = 2
TRACKING_SEARCH_AREA_MULTIPLIER = 8

class BuoysEntity(VisionEntity):

    name = "BuoysEntity"
    camera_name = "forward"

    def __init__(self, color_of_interest=BUOY_RED):
        self.color_of_interest = color_of_interest
        self.state = "searching"
        self.trackers = []
        self.buoy_locations = []

        self.saturation_adaptive_thresh_blocksize = 51
        self.saturation_adaptive_thresh = 15
        self.red_adaptive_thresh_blocksize = 51
        self.red_adaptive_thresh = 10

    def initialize_non_pickleable(self, debug=True):

            self.create_trackbar("saturation_adaptive_thresh", 50)
            self.create_trackbar("saturation_adaptive_thresh_blocksize", 50)
            self.create_trackbar("red_adaptive_thresh", 50)
            self.create_trackbar("red_adaptive_thresh_blocksize", 50)

    def find(self, frame, debug=True):

        # Scale image to reduce processing
        frame_scaled = cv.CreateImage((frame.width*0.5, frame.height*0.5), 8, 3)
        cv.Resize(frame, frame_scaled)
        cv.SetImageROI(frame, (0, 0, frame.width*0.5, frame.height*0.5))
        #scale_in_place(frame, (frame.width*0.5, frame.height*0.5))

        # debug_frame will be copied to frame at the end if debug=True
        if debug:
            debug_frame = cv.CloneImage(frame_scaled)
        else:
            debug_frame = False

        # Searching State
        # Search for buoys, then move to tracking when they are found
        if self.state == "searching":

            trackers = self.initial_search(frame_scaled, debug_frame)
            if trackers:
                self.trackers = trackers
                self.state = "tracking"
                print "Tracking"

                # Finish mission to make sure the first entity returned to
                # mission control has locations for all buoys
                self.buoy_locations = map(lambda x: adjust_location(x.object_center, frame_scaled.width, frame_scaled.height), self.trackers)
                if debug_frame:
                    cv.Copy(debug_frame, frame)
                return True

        # Tracking State
        num_buoys_found = 0
        if self.state == "tracking":
            num_buoys_found, locations = self.buoy_track(frame_scaled, self.trackers, debug_frame)
            if num_buoys_found > 0:
                self.buoy_locations = locations

        # Copy debug_frame
        if debug_frame:
            cv.Copy(debug_frame, frame)

        return num_buoys_found > 0

    def initial_search(self, frame, debug_frame):
        '''Search for buoys, return trackers when at least 2 are found.'''

        blobs, labeled_image = self.find_blobs(frame, debug_frame)
        buoy_blobs = self.extract_buoys_from_blobs(blobs, labeled_image)

        trackers = []
        if buoy_blobs:

            # Initialize Tracking
            for blob in buoy_blobs:
                tracker = libvision.Tracker(
                    frame,
                    blob.centroid,
                    (blob.roi[2]*TRACKING_TEMPLATE_MULTIPLIER,
                            blob.roi[3]*TRACKING_TEMPLATE_MULTIPLIER),
                    (blob.roi[2]*TRACKING_SEARCH_AREA_MULTIPLIER,
                            blob.roi[3]*TRACKING_SEARCH_AREA_MULTIPLIER),
                    min_z_score=TRACKING_MIN_Z_SCORE,
                    alpha=TRACKING_ALPHA,
                    #debug=True,
                )
                trackers.append(tracker)

        # Debug info
        if debug_frame and blobs:
            for blob in blobs:
                cv.Rectangle(debug_frame, (blob.roi[0], blob.roi[1]),
                         (blob.roi[0]+blob.roi[2], blob.roi[1]+blob.roi[3]), (0,255,0))

        return trackers

    def buoy_track(self, frame, trackers, debug_frame):
        '''Update trackers and return (num_buoys_found, buoy_locations).'''

        num_buoys_found = 0
        locations = []

        # Update trackers
        id_colors = ((0,255,0), (0,255,255), (255,255,0))
        for i, tracker in enumerate(trackers):
            location = tracker.locate_object(frame)

            if location:
                num_buoys_found += 1

                # Draw buoy on debug frame
                if debug_frame:
                    cv.Circle(debug_frame, location, 5, id_colors[i])

                locations.append(adjust_location(location, frame.width, frame.height))

            else:
                locations.append(False)

        return num_buoys_found, locations

    def extract_buoys_from_blobs(self, blobs, labeled_image):
        blobs = filter(self.blob_filter, blobs)
        if len(blobs) == 2 or len(blobs) == 3:
            return blobs

    def blob_filter(self, blob):
        if blob.size > 700:
            print "Filtering based on large blob size"
            return False

        width = blob.roi[2]
        height = blob.roi[3]
        ratio = width / height
        if ratio < 1:
            ratio = 1 / ratio
        if ratio > 2:
            print "Filtering based on aspect ratio"
            return False

        return True

    def find_blobs(self, frame, debug_image):
        '''Find blobs in an image.

        Hopefully this gets blobs that correspond with
        buoys, but any intelligent checking is done outside of this function.

        '''

        # Get Channels
        hsv = cv.CreateImage(cv.GetSize(frame), 8, 3);
        cv.CvtColor(frame, hsv, cv.CV_BGR2HSV)
        #saturation = libvision.misc.get_channel(hsv, 1)
        red = libvision.misc.get_channel(frame, 2)

        # Adaptive Threshold
        '''
        cv.AdaptiveThreshold(saturation, saturation,
            255,
            cv.CV_ADAPTIVE_THRESH_MEAN_C,
            cv.CV_THRESH_BINARY_INV,
            self.saturation_adaptive_thresh_blocksize - self.saturation_adaptive_thresh_blocksize%2 + 1,
            self.saturation_adaptive_thresh,
        )
        '''
        cv.AdaptiveThreshold(red, red,
            255,
            cv.CV_ADAPTIVE_THRESH_MEAN_C,
            cv.CV_THRESH_BINARY,
            self.red_adaptive_thresh_blocksize - self.red_adaptive_thresh_blocksize%2 + 1,
            -1*self.red_adaptive_thresh,
        )

        kernel = cv.CreateStructuringElementEx(9, 9, 4, 4, cv.CV_SHAPE_ELLIPSE)
        #cv.Erode(saturation, saturation, kernel, 1)
        #cv.Dilate(saturation, saturation, kernel, 1)
        cv.Erode(red, red, kernel, 1)
        cv.Dilate(red, red, kernel, 1)

        #buoys_filter = cv.CreateImage(cv.GetSize(frame), 8, 1)
        #cv.And(saturation, red, buoys_filter)
        buoys_filter = red

        if debug_image:
            #cv.NamedWindow("Saturation")
            #cv.ShowImage("Saturation", saturation)
            #cv.NamedWindow("Red")
            #cv.ShowImage("Red", red)
            cv.NamedWindow("AdaptiveThreshold")
            cv.ShowImage("AdaptiveThreshold", buoys_filter)

        # Get blobs
        labeled_image = cv.CreateImage(cv.GetSize(buoys_filter), 8, 1)
        blobs = libvision.blob.find_blobs(buoys_filter, labeled_image, MIN_BLOB_SIZE, 10)

        return blobs, labeled_image

    def __repr__(self):
        return "<BuoysEntity buoy_locations=%s>" % self.buoy_locations

def scale_in_place(image, new_size):
    '''Mutates image to have size of new_size.

    This function sets the ROI and copies a resized image into it.  Be aware
    that the image's ROI is set after returning from this function.

    '''
    copy = cv.CreateImage(cv.GetSize(image), 8, 3)
    cv.Copy(image, copy)
    cv.SetImageROI(image, (0, 0, new_size[0], new_size[1]))
    cv.Resize(copy, image, cv.CV_INTER_NN)

def adjust_location(location, width, height):
    '''
    Move origin to center and flip along horizontal axis.  Right
    and up will then be positive, which makes more sense for
    mission control.
    '''
    return Point(
        location[0] - width/2,
        -1*location[1] + height/2
    )

