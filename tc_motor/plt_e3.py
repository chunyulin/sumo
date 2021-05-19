from __future__ import absolute_import
from __future__ import print_function

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

    #<interval begin="0.00" end="150.00" id="e3_A0" meanTravelTime="27.93" meanOverlapTravelTime="28.57" meanSpeed="12.58" meanHaltsPerVehicle="0.39" meanTimeLoss="14.21" vehicleSum="36" meanSpeedWithin="7.42" meanHaltsPerVehicleWithin="0.84" meanDurationWithin="49.01" vehicleSumWithin="63" meanIntervalSpeedWithin="7.42" meanIntervalHaltsPerVehicleWithin="0.84" meanIntervalDurationWithin="49.01" meanTimeLossWithin="36.65"/>

    if options.summary is None:
        print("Error: at least one summary file must be given")
        sys.exit(1)

    files = options.summary.split(",")
    
    tid=2
    cols = ["begin","end","id",
            "meanTravelTime","meanOverlapTravelTime","meanSpeed",
            "meanHaltsPerVehicle","meanTimeLoss","vehicleSum","meanSpeedWithin","meanHaltsPerVehicleWithin", "meanDurationWithin","vehicleSumWithin","meanIntervalSpeedWithin","meanIntervalHaltsPerVehicleWithin","meanIntervalDurationWithin",               "meanTimeLossWithin" ]
   
    print(cols)
    label = cols[0:tid]+cols[tid+1:]
    
    data = {}
    for raw in sumolib.xml.parse_fast(files[0], "interval", cols ):
        id = raw[tid]
        if id not in data:
            print("Adding ..", id)
            data[id] = []
        data[id].append( [ float(x) for x in raw[0:tid]+raw[tid+1:] ] )
    
    fig = plt.figure()
    for k in data:
        #tag="e3{:02d}".format(i)
        tag=k
        d = np.array(data[k])
        t = d[:,0]

        plt.plot(t, d[:,2], label=label[2])
        plt.plot(t, d[:,3], label=label[3])
        plt.plot(t, d[:,6], label=label[6])
        plt.plot(t, d[:,10], label=label[10])
        plt.plot(t, d[:,11], label=label[11])
        plt.plot(t, d[:,14], label=label[14])
        plt.plot(t, d[:,15], label=label[15])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_time.jpg".format(tag))
        plt.clf()
        
        plt.plot(t, d[:,4], label=label[4])
        plt.plot(t, d[:,8], label=label[8])
        plt.plot(t, d[:,9], label=label[9])
        plt.plot(t, d[:,12], label=label[12])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_vel.jpg".format(tag))
        plt.clf()
   
        plt.plot(t, d[:,5], label=label[5])
        plt.plot(t, d[:,7], label=label[7])
        plt.plot(t, d[:,13], label=label[13])
        plt.xlabel("Time/s")
        plt.legend()
        plt.savefig("{}_flow.jpg".format(tag))
        plt.clf()
   



if __name__ == "__main__":
    sys.exit(main(sys.argv))
