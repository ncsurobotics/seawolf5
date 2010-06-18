//header for mission-related files 
#ifndef __SEAWOLF_VISION_MISSION_INCLUDE_H
#define ___SEAWOLF_VISION_MISSION_INCLUDE_H

#include <stdbool.h>
#include <highgui.h>
#include <opencv/cv.h>

// Misc Constants
#define PI 3.141592653589793238462643383279502884197169399375105820974944592307816406286208998
#define MAX_PHI   20
#define MAX_RHO   50

/**
 * mission_output
 * This structure is passed into and also returned from every mission.
 */
struct mission_output {

    // Yaw
    // yaw_control can be one of the following:
    // ROT_MODE_ANGULAR
    //     "yaw" is interpreted as a desired IMU heading.
    // ROT_MODE_RELATIVE
    //     "yaw" is interpreted as desired change in the current IMU heading
    // ROT_MODE_RATE
    //     "yaw" is interpreted as a desired turning rate (degrees per second)
    float yaw_control;
    float yaw;  // Angle

    // Speed
    float rho;

    // Depth
    // Control for depth is either absolute or relative.  So "depth_control"
    // can be one of the following:
    // DEPTH_ABSOLUTE
    //     "depth" is interpreted as distance relative to the surface.
    // DEPTH_RELATIVE
    //     "depth" is interpreted as a desired change in depth relative to the
    //     craft.
    float depth_control;
    float depth;

    // Missions should set this to the frame they recieved from the camera, so
    // main.c can use it for debugging.  Missions may also write debug
    // information on this image and it will be displayed.
    IplImage* frame;

    // This flag is set to true inside a mission when the mission is completed.
    // main.c notices when this is set to true and switches to the next
    // mission.
    bool mission_done;

};

/********* Mission Definitions **********/
// Mission Constants
#define MISSION_WAIT 0
#define MISSION_GATE 1
#define MISSION_BOUY 3
#define MISSION_HEDGE 4
#define MISSION_WINDOW 5
#define MISSION_WEAPONS_RUN 6
#define MISSION_MACHETE 7
#define MISSION_BRIEFCASE_GRAB 77
#define MISSION_OCTOGON 8
#define MISSION_ALIGN_PATH 9
#define MISSION_STOP 10

static const char* mission_strings[] = {
    [MISSION_WAIT] = "WAIT",
    [MISSION_GATE] = "GATE",
    [MISSION_BOUY] = "BOUY",
    [MISSION_HEDGE] = "HEDGE",
    [MISSION_WINDOW] = "WINDOW",
    [MISSION_WEAPONS_RUN] = "WEAPONS_RUN",
    [MISSION_MACHETE] = "MACHETE",
    [MISSION_BRIEFCASE_GRAB] = "BRIEFCASE_GRAB",
    [MISSION_OCTOGON] = "OCTOGON",
    [MISSION_STOP] = "STOP",
    [MISSION_ALIGN_PATH] = "ALIGN_PATH"
};

// Gives the order which the missions are executed.  The initial mission
// defaults to 0, but can be changed in debug.mk
static const int mission_order[] = {
    MISSION_WAIT,
    MISSION_GATE,
    MISSION_BOUY,
    MISSION_ALIGN_PATH,
    MISSION_HEDGE,
    MISSION_WINDOW,
    MISSION_WEAPONS_RUN,
    MISSION_MACHETE,
    MISSION_BRIEFCASE_GRAB,
    MISSION_OCTOGON,
    MISSION_WAIT,
};

/*********** Mission Prototypes **************/
/*** Gate ***/
void mission_gate_init(IplImage* frame, double depth);
struct mission_output mission_gate_step(struct mission_output);

/*** Bouy ***/
void mission_bouy_init(IplImage* frame);
struct mission_output mission_bouy_step(struct mission_output);

//internal bouy functions
int bouy_first_approach(void);

void bouy_bump_init(void);
int bouy_bump(struct mission_output* result, RGBPixel* color);

/*** Weapons Run ***/
void mission_weapons_init(void);
struct mission_output mission_weapons_step(struct mission_output);

/*** Path ***/
void mission_align_path_init(IplImage* frame, struct mission_output* results);
struct mission_output mission_align_path_step(struct mission_output);

// ---- Window ---- //
void mission_window_init(IplImage* frame);
struct mission_output mission_window_step(struct mission_output);

#endif
