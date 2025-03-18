# adapted from previous iteration's implementation
# https://github.com/mylescoding/ssl07-2324/blob/main/README.md

import math
import os
import sys
import optparse
import warnings

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options

def run():

    step = 0

    old_kuf_phase = 0
    old_kbt_phase = 0
    while traci.simulation.getMinExpectedNumber() > 0:

        # insert code for switching phases/greentime here based on the model/approach
        # add helper functions to the code as necessary
        
        """
        if(traci.trafficlight.getPhase("kuf") in [0,3,6,9]):
            kuf_phase = traci.trafficlight.getPhase("kuf")
            kuf_phase_name = traci.trafficlight.getPhaseName("kuf")
        if(kuf_phase != old_kuf_phase):
            print("CURRENT PHASE AND NAME FOR KUF: " + str(kuf_phase) + " : " + str(kuf_phase_name))    

            vehicle_count_dict = getLaneParams()
            print(f"bianckkks")
            print(vehicle_count_dict)
            kuf_phase_name = traci.trafficlight.getPhaseName("kuf")
            print(f"kuf_phase_name is: " + kuf_phase_name)
            print(f"calling helper function now!")
            greentime = helper_function(kuf_phase_name,vehicle_count_dict)
            print(f"greentime returned by helper_function! green time is: " + str(greentime) + str(type(greentime)))

            traci.trafficlight.setPhaseDuration("kuf", greentime)   
            traci.trafficlight.setPhaseDuration("kbt", greentime)   
            
            print(f"Phase and Duration for KUF: " + str(traci.trafficlight.getPhaseName("kuf"))+ ", "+str(traci.trafficlight.getPhaseDuration("kuf")) )
            print(f"Phase and Duration for KBT: " + str(traci.trafficlight.getPhaseName("kbt"))+ ", "+str(traci.trafficlight.getPhaseDuration("kbt")) )

            #this tracks green changes in KUF
        old_kuf_phase = kuf_phase
        """
        traci.simulationStep() # move one second in simulation
        

    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "-c", "osm.sumocfg",
                 "--tripinfo-output", "tripinfo.xml"])
    # getLaneParams()

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        run()