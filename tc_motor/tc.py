#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import numpy as np
import random
import optparse
import colorsys
import re

import pyqubo
import neal
from pyqubo import Binary
from pyqubo import Array

from sumolib import checkBinary
import traci


NUM_PHASE=12  ### Total number of phases
NSET = 3      ### Number of phases in a group (3 for G/Y/R)
OPT_PERSEC = 10
    
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--qubo", action="store_true", default=False)
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    optParser.add_option("--nogenflow", action="store_true",
                         default=False, help="Don't regenerate flow files")
    optParser.add_option("-p",  action="store", type="string", dest="prog",default="real")
    optParser.add_option("--dt",  action="store", type="float", dest="dt",default=0.5)
    optParser.add_option("--end",  action="store", type="float", dest="end",default=3600)
    options, args = optParser.parse_args()
    return options

def gen_flow_from_od(vtype, outflow, taz, od, scale = 1):
	os.system("od2trips --vtype={} --prefix={} --taz-files={} --od-matrix-files={} --flow-output={} --scale={} --verbose=true --departpos=random".format(vtype, vtype, taz, od, outflow, scale))	

def measure():
    
    coeff_list = np.zeros(4)
    ## ( -coff * m0 )
    coeff_list[0] = traci.multientryexit.getLastStepVehicleNumber('top') + \
                    traci.multientryexit.getLastStepVehicleNumber('bottom')
    coeff_list[1] = traci.multientryexit.getLastStepVehicleNumber('top')    * 0.3 + \
                    traci.multientryexit.getLastStepVehicleNumber('bottom') * 0.3   ## assume 20% for left-turn
    coeff_list[2] = traci.multientryexit.getLastStepVehicleNumber('right')
    coeff_list[3] = traci.multientryexit.getLastStepVehicleNumber('left')
    return coeff_list

def output_flow(t):
    print("== t: {:5}  {:4} {:4} {:4} {:4}".format(t, 
            traci.multientryexit.getLastStepVehicleNumber('top'),
            traci.multientryexit.getLastStepVehicleNumber('bottom'),
            traci.multientryexit.getLastStepVehicleNumber('right'),
            traci.multientryexit.getLastStepVehicleNumber('left') )
          )            
   
    
x = Array.create('x', shape=(4), vartype='BINARY')
Q_mode_constrain = (1 - sum(x))**2
def qubo(Coeff):
    #print("      Coeff: {}".format(Coeff) )
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
            # return 0,3,6,9        
            return NSET*int(key[2:-1]) 
    
            
def run(end_time, d_time, isopt):

    TLSs = traci.trafficlight.getIDList()  # [A0]
    E3s = traci.multientryexit.getIDList()
    print ("E3s: ", E3s)
    
    dt = dict()
    gt = dict()
    nextphase = dict()
    duration  = dict()
    for s in TLSs:
        dt[s]        = 3     ## transition time
        gt[s]        = 25    ## minimal green/red  time
        nextphase[s] = 0     ## next phase, startrf from 0
        duration[s]  = 0     ## how long the current phase has been
        
    step = 0
    OPT_STEP = int(OPT_PERSEC / d_time)
    
    while step <= end_time / d_time:

        time = step * d_time
        if step % 100 == 0: 
            output_flow(time)

        traci.simulationStep()
        step += 1

        if not isopt: continue
        
        # first, check the minimal duraiton for stability
        run_opt = False
        for s in TLSs:
            traci.trafficlight.setPhase(s, nextphase[s])
            if nextphase[s]%NSET>0:     ## if next is 'y|r', fixed time for yellow
                if duration[s] <= dt[s] : 
                    duration[s] += d_time
                else: 
                    nextphase[s] = (nextphase[s] + 1)%NUM_PHASE
                    duration[s] = 0
                continue    
            else:                        ## if next is 'g', check minimal time for red/green
                duration[s] += d_time
                if duration[s] <= gt[s] : 
                    continue    
                else:                    ## only than to run the optimizer
                    duration[s] += d_time
                    run_opt = True

        if run_opt and (step%OPT_STEP == 0):
            #print("=== Step: {:5}  # Car: {}".format(step, traci.vehicle.getIDCount()))
            Coeff = measure()
            opt_qubo  = qubo(Coeff)
            opt_phase = qubo2phase(opt_qubo) 
            
            for s in TLSs:
                current_phase = traci.trafficlight.getPhase(s)
                
                # if the qubo tell signle should be changed
                if abs(opt_phase - current_phase) > NSET-1:
                    nextphase[s] = (current_phase + 1)%NUM_PHASE
                    duration[s] = 0
                    
       
       
def showTLS(tid):   
    print("=== Traffic light ID : {} ===".format(tid))
    p = traci.trafficlight.getProgram(tid)
    print("Current program : ", p)
    print("Current Phase   : ", traci.trafficlight.getPhase(tid))
    print("State           : ", traci.trafficlight.getRedYellowGreenState(tid)) 

    progs = traci.trafficlight.getAllProgramLogics(tid)
    for p in progs:
        print("Program name: ", p.programID)
        co = 0
        for m in p.phases:
            print (" {:2d}: {}".format(co, m.state))
            co +=1

def showConnAt(tid):
    print("=== Connnections at {} ===".format(tid))
    links = traci.trafficlight.getControlledLinks(tid)
    co=0
    for li in links:
      print (" {:2d}: {}".format(co, li))
      co +=1
        
def showNet():
    print("=== Basic network information ===")
    print("  # of Edges: ", len(traci.edge.getIDList()))
    print("  # of Junctions: ", len(traci.junction.getIDList()))
    tls = traci.trafficlight.getIDList()
    print("  Traffic Lights: ", tls)


if __name__ == "__main__":
    options = get_options()

    if not options.nogenflow:
        gen_flow_from_od("car",     "gen.car.flow.xml",     "taz.add.xml", "od.txt",    1)
        gen_flow_from_od("motor",   "gen.motor.flow.xml",   "taz.add.xml", "od.txt",  0.7)    
        gen_flow_from_od("truck",   "gen.truck.flow.xml",   "taz.add.xml", "od.txt",  0.05)
        gen_flow_from_od("trailer", "gen.trailer.flow.xml", "taz.add.xml", "od.txt",  0.03)

    sumoBinary = checkBinary('sumo-gui')
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    
    traci.start([sumoBinary, "-c", "tc.sumocfg", "--step-length={}".format(options.dt),
        "--statistic-output=stat.log",  "--summary=summary.log",
        "--lateral-resolution=1.1", "--threads=1", "--ignore-junction-blocker=-1"])
	    #  , "--summary=summary.log", "--default.action-step-length=2", "--collision-output=collision.log",, "--full-output=full.log",
    traci.trafficlight.setProgram("A0", options.prog)
    showNet()
    showConnAt("A0")
    showTLS("A0")
    
    run(options.end, options.dt, options.qubo)
    traci.close()
    sys.stdout.flush()

