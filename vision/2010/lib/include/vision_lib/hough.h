#ifndef __SEAWOLF_VISION_LIB_HOUGH_INCLUDE_H
#define __SEAWOLF_VISION_LIB_HOUGH_INCLUDE_H

void hough_init(void);
void houghMouseDraw(int event, int x, int y, int flags, void* param);
CvSeq* hough(IplImage* img, IplImage* original, int threshold, int linesMax,int targetAngle, int angleThreshold, int clusterSize, int clusterWidth, int clusterHeight);
void hough_free(void);

#endif
