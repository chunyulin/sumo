from __future__ import absolute_import
from __future__ import print_function

#  Lanearea Detectors (E2)

import os
import sys

sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import sumolib
from sumolib.visualization import helpers
import matplotlib.pyplot as plt
import numpy as np
from collections import OrderedDict

def main(args=None):
    """The main function; parses options and plots"""
    # ---------- build and read options ----------
    from optparse import OptionParser
    optParser = OptionParser()
    optParser.add_option("-i", "--summary-inputs", dest="summary", metavar="FILE",
                         help="Defines the summary-output files to use as input")
    helpers.addInteractionOptions(optParser)
    helpers.addPlotOptions(optParser)
    options, _ = optParser.parse_args(args=args)

    #"begin",end="150.00" id="e2det_109505014#6.100_0" sampledSeconds="33.11" nVehEntered="3" nVehLeft="2" nVehSeen="3" meanSpeed="12.46" meanTimeLoss="2.76" meanOccupancy="0.34" maxOccupancy="3.08" meanMaxJamLengthInVehicles="0.02" meanMaxJamLengthInMeters="0.05" maxJamLengthInVehicles="1" maxJamLengthInMeters="2.10" jamLengthInVehiclesSum="7" jamLengthInMetersSum="14.70" meanHaltingDuration="4.50" maxHaltingDuration="4.50" haltingDurationSum="4.50" meanIntervalHaltingDuration="4.50" maxIntervalHaltingDuration="4.50" intervalHaltingDurationSum="4.50" startedHalts="1.00" meanVehicleNumber="0.23" maxVehicleNumber="2" />

    if options.summary is None:
        print("Error: at least one summary file must be given")
        sys.exit(1)

    files = options.summary.split(",")
    
    tid=2
    cols = ["begin","end","id",     
             "sampledSeconds","nVehEntered","nVehLeft","nVehSeen",                                   
             "meanSpeed","meanTimeLoss","meanOccupancy","maxOccupancy","meanMaxJamLengthInVehicles",
             "meanMaxJamLengthInMeters","maxJamLengthInVehicles","maxJamLengthInMeters","jamLengthInVehiclesSum","jamLengthInMetersSum",
             "meanHaltingDuration","maxHaltingDuration","haltingDurationSum","meanIntervalHaltingDuration","maxIntervalHaltingDuration", "intervalHaltingDurationSum","startedHalts","meanVehicleNumber","maxVehicleNumber" ]
    
    print(cols)
    label = cols[0:tid]+cols[tid+1:]
    
    data = {}
    for raw in sumolib.xml.parse_fast(files[0], "interval", cols ):
        id = raw[tid]
        if id not in data:
            data[id] = []
        data[id].append( [ float(x) for x in raw[0:tid]+raw[tid+1:] ] )
    
    fig = plt.figure()
    for i, k in enumerate(data):
        tag="e2{:02d}".format(i)
        d = np.array(data[k])
        t = d[:,0]

        plt.plot(t, d[:,7], label=label[7])
        plt.plot(t, d[:,8], label=label[8])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_occ.jpg".format(tag))
        plt.clf()
        
        plt.plot(t, d[:,6], label=label[6])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_vel.jpg".format(tag))
        plt.clf()
   
        plt.plot(t, d[:,15], label=label[15])
        plt.plot(t, d[:,16], label=label[16])
        plt.plot(t, d[:,17], label=label[17])
        plt.plot(t, d[:,18], label=label[18])
        plt.plot(t, d[:,19], label=label[19])
        plt.plot(t, d[:,20], label=label[20])
        plt.plot(t, d[:,21], label=label[21])
        plt.plot(t, d[:,22], label=label[22])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_flow.jpg".format(tag))
        plt.clf()
   



if __name__ == "__main__":
    sys.exit(main(sys.argv))
