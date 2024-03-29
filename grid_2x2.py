#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random
import colorsys
import pyqubo

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa


def gen_grid(fname, lanes):
	#os.system("netgenerate  -j traffic_light -S 20 -o {} --grid --grid.number=2  -L{} --grid.length=200 --grid.attach-length=200".format(fname, lanes))  
    os.system("netgenerate --tls.guess -S 20 -o {} --grid --grid.number=2  -L{} --grid.length=700 --grid.attach-length=300 --turn-lanes 1 --turn-lanes.length 100 --tls.left-green.time 10".format(fname, lanes))
    # max 20 m/s
		
def gen_taz(afile):
    with open(afile, "w") as f:
        print("""<additional>
		         <tazs>
                   <taz id="left">
                     <tazSource id="left0A0" weight="0.9"/><tazSource id="left1A1" weight="0.5"/>
                     <tazSink id="A0left0" weight="0.5"/>  <tazSink id="A1left1" weight="0.5"/>
                   </taz>
                   <taz id="top">
                     <tazSource id="top0A1" weight="0.5"/><tazSource id="top1B1" weight="0.5"/>
                     <tazSink id="A1top0" weight="0.5"/>  <tazSink id="B1top1" weight="0.5"/>
                   </taz>
                   <taz id="right">
                     <tazSource id="right0B0" weight="0.5"/><tazSource id="right1B1" weight="0.5"/>
                     <tazSink id="B0right0" weight="0.5"/>  <tazSink id="B1right1" weight="0.5"/>
                   </taz>
                   <taz id="bottom">
                     <tazSource id="bottom0A0" weight="0.5"/><tazSource id="bottom1B0" weight="0.5"/>
                     <tazSink id="A0bottom0" weight="0.5"/>  <tazSink id="B0bottom1" weight="0.5"/>
                   </taz>
                 </tazs>
				 </additional>""", file=f)

def gen_flow_from_od(outflow, taz, od):
	os.system("od2trips.exe --taz-files {} --od-matrix-files {} --flow-output {}".format(taz, od, outflow))	
    ### generate trip instead of flow:   od2trips  -d .\od.txt -n .\taz.xml -o trip.gen.xml 
    ### duarouter --route-files=.\trip.gen.xml --net-file=.\net.net.xml --output-file=route.gen.xml --taz-files=.\taz.xml --with-taz

def info():

    edges=traci.edge.getIDList()
    for e in edges:
        if e[0]!=':': 
            print(" E: ", e)
            
    tls = traci.trafficlight.getIDList()
    for t in tls:
       #clanes = traci.trafficlight.getControlledLanes(t)
       #for clane in clanes: print("    Lane: ", clane)
       print("=== TL: ", t)
       phases = traci.trafficlight.getAllProgramLogics(t)[0].getPhases()
       for p in phases:
            print(p.state)
       
       clinks = traci.trafficlight.getControlledLinks(t)
       for cl in clinks:
            print("    Link: ", cl)
            
    juncs = traci.junction.getIDList()
    for j in juncs:
        if j[0]!=':': print(" J: ",j)
        
def update_carstat():
   cars = traci.vehicle.getIDList()
   for c in cars:
     v = traci.vehicle.getSpeed(c)/ traci.vehicle.getMaxSpeed(c)
     r,g,b = colorsys.hsv_to_rgb(1-v, 1.0, 1.0)
     traci.vehicle.setColor(c, (255*r, 255*g, 255*b))	  	

def measure():
    edges = traci.edge.getIDList()
    n = list(map(traci.edge.getLastStepVehicleNumber, edges))
    print(" -- #car: ",  list(map(traci.edge.getLastStepVehicleNumber, edges)))

tls = ["A0", "A1", "B0", "B1"]		
def control():
    print(" -- TL modes: ", list(map(traci.trafficlight.getPhase, tls)))

def run():
    """execute the TraCI control loop"""

    step = 0
    while step < 3600:
        traci.simulationStep()
        update_carstat()
        if step%5 == 0: 
          print("Step: {:5}  # Car: {}".format(step, traci.vehicle.getIDCount()))
          #measure()
        
        #if step%10 == 0: control()
        step += 1
    
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    lanes = 2
    gen_grid("gen.net.xml", lanes)
    gen_taz("gen.taz.xml")
    gen_flow_from_od("gen.flow.xml", "gen.taz.xml", "od.txt")

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
     
    traci.start([sumoBinary, "-c", "main.sumocfg", "--statistic-output" , "stat.log"])

    info()

    run()
	
