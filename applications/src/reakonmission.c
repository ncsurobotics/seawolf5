
#include "seawolf.h"

int main(void) {
    Seawolf_loadConfig("../conf/seawolf.conf");
    Seawolf_init("Mission Controller");

    //Notify_filter(FILTER_ACTION, "MISSIONTRIGGER");
    //Notify_get(NULL, NULL);

    Notify_send("THRUSTER_REQUEST", Util_format("Forward %d %d", 0, 0));
    Var_set("Rot.Angular.Target", 50.0);
    //Notify_send("THRUSTER_REQUEST", Util_format("Forward %d %d", 40, 40));

    Seawolf_close();
    return 0;
}
