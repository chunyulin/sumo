# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 11:33:37 2021

@author: Amit
"""

#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import numpy as np
import random
import optparse
import colorsys
import pyqubo
from sumolib import checkBinary  # noqa
import traci  # noqa
import neal
from pyqubo import Binary
from pyqubo import Array
import re

#stdoutOrigin=sys.stdout 
#sys.stdout = open("log.txt", "w")
# including SUMO PYTHONPATH
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


def gen_grid(fname, lanes):
	#os.system("netgenerate  -j traffic_light -S 20 -o {} --grid --grid.number=2  -L{} --grid.length=200 --grid.attach-length=200".format(fname, lanes))  
    os.system("netgenerate --tls.guess -S 20 -o {} --grid --grid.number=1  -L{} --grid.length=700 --grid.attach-length=500 --turn-lanes 1 --turn-lanes.length 150 --tls.left-green.time 20  --tls.green.time 20 --check-lane-foes.all=true --no-turnarounds=true".format(fname, lanes))
    # max 20 m/s ~ (~ 75 km/h)

def gen_flow_from_od(vtype, outflow, taz, od, scale = 1):
	os.system("od2trips --vtype={} --prefix={} --taz-files={} --od-matrix-files={} --flow-output={} --scale={} --verbose=true --departpos=random"
        .format(vtype, vtype, taz, od, outflow, scale))	
    ### generate trip instead of flow:   od2trips  -d .\od.txt -n .\taz.xml -o trip.gen.xml 
    ### duarouter --route-files=.\trip.gen.xml --net-file=.\net.net.xml --output-file=route.gen.xml --taz-files=.\taz.xml --with-taz

    
def info():
    print("##### Edges: ", traci.edge.getIDList())
    print("##### Junctions: ", traci.junction.getIDList())
    tls = traci.trafficlight.getIDList()
    print("##### Traffic Light: ", tls)
    print("#####  TL modes: ", list(map(traci.trafficlight.getPhase, tls)))
    for t in tls:
       print(" --",t, ":", traci.trafficlight.getAllProgramLogics(t))

    #mode = traci.trafficlight.getPhase("A0")  ## get the current mode. In four-junction case, the junction node is named 
       
def update_color():
   cars = traci.vehicle.getIDList()
   for c in cars:
     v = traci.vehicle.getSpeed(c)/ traci.vehicle.getMaxSpeed(c)
     r,g,b = colorsys.hsv_to_rgb(1-v, 1.0, 1.0)
     traci.vehicle.setColor(c, (255*r, 255*g, 255*b))	  	

def measure():
    #edges = traci.edge.getIDList()
    #lanes = traci.lane.getIDList()
    coeff_list = np.zeros(4)
    ## waiting TD           ( -coff * m0 )
    coeff_list[0] = traci.lane.getLastStepVehicleNumber('top0A0.350.00_0') + \
                    traci.lane.getLastStepVehicleNumber('top0A0.350.00_1') + \
                    traci.lane.getLastStepVehicleNumber('bottom0A0.350.00_0') + \
                    traci.lane.getLastStepVehicleNumber('bottom0A0.350.00_1')
    ## waiting TD left-turn ( -coff * m2 )                
    coeff_list[1] = traci.lane.getLastStepVehicleNumber('top0A0.350.00_2') + \
                    traci.lane.getLastStepVehicleNumber('bottom0A0.350.00_2')
    ## waiting LR           ( -coff * m4 ) ## more car stuck behind, more probable the phase is
    coeff_list[2] = traci.lane.getLastStepVehicleNumber('left0A0.350.00_0') + \
                    traci.lane.getLastStepVehicleNumber('left0A0.350.00_1') + \
                    traci.lane.getLastStepVehicleNumber('right0A0.350.00_0') + \
                    traci.lane.getLastStepVehicleNumber('right0A0.350.00_1')
    ## waiting LR left-turn ( -coff * m6 )
    coeff_list[3] = traci.lane.getLastStepVehicleNumber('left0A0.350.00_2') + \
                    traci.lane.getLastStepVehicleNumber('right0A0.350.00_2')
    ## TODO: try other functions like"
    # getLastStepHaltingNumber(e)
    # getLastStepOccupancy(e)
    # getLastStepMeanSpeed(e)
    # traci.lane.getMaxSpeed(l)  # only for lane
    
    return coeff_list


x = Array.create('x', shape=(4), vartype='BINARY')
Q_mode_constrain = (1 - sum(x))**2
def qubo(Coeff):
    print("      Coeff: {}".format(Coeff) )
    lamda1 = -1; lamda4 = 100;
    Q1 = sum(x*Coeff)
    H = lamda1*Q1 + lamda4*Q_mode_constrain
    model = H.compile()
    bqm = model.to_bqm()
    sa = neal.SimulatedAnnealingSampler()
    sampleset = sa.sample(bqm, num_reads=20)
    decoded_samples = model.decode_sampleset(sampleset)
    best_sample = min(decoded_samples, key=lambda x: x.energy)
    opt = best_sample.sample
    #print("SA-Opt:{}  Energy:{}".format(best_sample.sample, best_sample.energy) )
    ## Q: Is it possiable to have more than one activate mode in a junction if lambda4 is too small ? 
    ## Do we have to check that ?
    
    return opt
    
def qubo2phase(qubo):
    for key in qubo:   ## x_{0j}
        if qubo[key] == 1:
            # return 0,2,4,6        
            return 2*int(key[2:-1]) 
    
            
def run():

    NUM_PHASE=8
    TLSs = traci.trafficlight.getIDList()  # [A0, A1, B0, B1]
    
    dt = dict()
    gt = dict()
    nextphase = dict()
    duration  = dict()
    for s in TLSs:
        dt[s]        = 5     ## transition time
        gt[s]        = 30    ## minimal green/red  time
        nextphase[s] = 0     ## next phase
        duration[s]  = 0     ## how long it has been in "cphase"
        
    info()
    step = 0
    while step < 3600:
    
        traci.simulationStep()
        update_color()
        step += 1
       
        # first, check the minimal duraiton for stability
        run_opt = False
        for s in TLSs:
            traci.trafficlight.setPhase(s, nextphase[s])
            if nextphase[s]%2==1:        ## fixed time for yellow
                if duration[s] <= dt[s] : 
                    duration[s] += 1
                else: 
                    nextphase[s] = (nextphase[s] + 1)%NUM_PHASE
                    duration[s] = 0
                continue    
            else:                        ## minimal time for red/green
                duration[s] += 1
                if duration[s] <= gt[s] : 
                    continue    
                else: 
                    duration[s] += 1
                    run_opt = True

        if run_opt and (step%5 == 0):
            print("=== Step: {:5}  # Car: {}".format(step, traci.vehicle.getIDCount()))

            Coeff = measure()
            opt_qubo  = qubo(Coeff)
            opt_phase = qubo2phase(opt_qubo) 
            
            for s in TLSs:
                current_phase = traci.trafficlight.getPhase(s)
                
                # if the qubo tell signle should be changed
                if abs(opt_phase - current_phase) > 1:
                    nextphase[s] = (current_phase + 1)%NUM_PHASE
                    duration[s] = 0
                    
    
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    options = get_options()

    if 0:    
      lanes = 4
      #gen_grid("gen.net.xml", lanes)                              # gen network file
    gen_flow_from_od("car",     "gen.car.flow.xml",     "motor.taz.xml", "od.txt", 1)
    gen_flow_from_od("motor",   "gen.motor.flow.xml",   "motor.taz.xml", "od.txt", 1)    
    gen_flow_from_od("truck",   "gen.truck.flow.xml",   "motor.taz.xml", "od.txt", 0.02)
    gen_flow_from_od("trailer", "gen.trailer.flow.xml", "motor.taz.xml", "od.txt", 0.0001)

    sumoBinary = checkBinary('sumo-gui')
    traci.start([sumoBinary, "-c", "main.sumocfg", "--statistic-output" , "stat.log", "--lateral-resolution=1.0", "--threads=2"])
	
    run()
    traci.close()
    sys.stdout.flush()

