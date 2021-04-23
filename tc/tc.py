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

def gen_flow_from_od(outflow, taz, od):
	os.system("od2trips.exe --taz-files {} --od-matrix-files {} --flow-output {}".format(taz, od, outflow))	
    
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
        """
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
        """            
    
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    options = get_options()

    gen_flow_from_od("gen.flow.xml", "taichung.taz.xml", "od.txt")   # gen flow demand

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    traci.start([sumoBinary, "-c", "main.sumocfg", "--statistic-output" , "stat.log"])
	
    run()
    traci.close()
    sys.stdout.flush()

