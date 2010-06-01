
#include "seawolf.h"

#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <signal.h>

/* Top level Seawolf directory */
#define SEAWOLF_DIR "../"
#define MAX_ARGS 31

/* Run an application with the given NULL terminated argument list. The
   application will fork into the background and the current program will
   resume. The PID of the spawned application is returned. */
static int spawn(char* path, char* args, ...) {
    int pid;
    va_list ap;
    char* argv[MAX_ARGS + 1];

    /* Build arguments array */
    argv[0] = path;
    va_start(ap, args);
    for(int i = 1; i < MAX_ARGS && args != NULL; i++) {
        argv[i] = args;
        argv[i+1] = NULL;
        args = va_arg(ap, char*);
    }
    va_end(ap);

    /* Run program */
    pid = fork();
    if(pid == 0) {
        /* Replace current process with the given application */
        execv(path, argv);
        
        /* Should *not* happen */
        fprintf(stderr, "Application %s failed to spawn!\n", path);
        exit(EXIT_FAILURE);
    }

    return pid;
}

int main(int argc, char** argv) {
    Seawolf_loadConfig("../conf/seawolf.conf");
    Seawolf_init("Conductor");

    /* PIDs of all spawned applications */
    int pid[8];

    Notify_filter(FILTER_ACTION, "MISSIONTRIGGER");

    while(true) {
        Var_set("PortX", 0);
        Var_set("StarX", 0);
        Var_set("PortY", 0);
        Var_set("StarY", 0);
        Var_set("Aft", 0);
        
        /* Move to vision directory */
        chdir("../vision/2010/");
        pid[0] = spawn("./main", argv[1], argv[2], NULL);
        
        Notify_get(NULL, NULL);
        for(int i = 3; i > 0; i--) {
            Logging_log(DEBUG, Util_format("Preparing to start - %d", i));
            Util_usleep(1);
        }
        
        chdir("../../applications/");
        pid[1] = spawn("./bin/depthpid", NULL);
        pid[2] = spawn("./bin/rotpid", NULL);
        
        Util_usleep(1);
        pid[7] = spawn("./bin/mixer", NULL);
        
        Notify_get(NULL, NULL);
        Logging_log(DEBUG, "Killing...");
        kill(pid[0], SIGTERM);
        kill(pid[1], SIGTERM);
        kill(pid[2], SIGTERM);
        kill(pid[7], SIGTERM);
        Util_usleep(1.0);
    }

    Seawolf_close();
    return 0;
}
