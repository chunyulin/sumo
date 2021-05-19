from __future__ import absolute_import
from __future__ import print_function

# Induction Loops Detectors (E1)

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

    #<interval begin="90.00" end="120.00" id="e1det_886398487#2.123_3" nVehContrib="0" flow="0.00" occupancy="0.00" speed="-1.00" harmonicMeanSpeed="-1.00" #length="-1.00" nVehEntered="0"/>    
    
    if options.summary is None:
        print("Error: at least one summary file must be given")
        sys.exit(1)

    files = options.summary.split(",")
    
    tid=2
    cols = ["begin", "end", "id", "nVehContrib", "flow", "occupancy", "speed", "harmonicMeanSpeed", "length", "nVehEntered" ]
    label = cols[0:tid]+cols[tid+1:]
    
    data = {}
    for raw in sumolib.xml.parse_fast(files[0], "interval", cols ):
        id = raw[tid]
        
        if id not in data:
            print("Adding ..", id)
            data[id] = []
        data[id].append( [ float(x) for x in raw[0:tid]+raw[tid+1:] ] )
    
    fig = plt.figure()
    for i, k in enumerate(data):
        tag="e1{:02d}".format(i)
        d = np.array(data[k])
        t = d[:,0]

        plt.plot(t, d[:,4], label=label[4])
        plt.savefig("{}_occ.jpg".format(tag))
        plt.xlabel("Time/s")
        plt.legend()
        plt.clf()
        
        plt.plot(t, d[:,5], label=label[5])
        plt.plot(t, d[:,6], label=label[6])
        plt.savefig("{}_vel.jpg".format(tag))
        plt.xlabel("Time/s")
        plt.legend()
        plt.clf()
   
        plt.plot(t, d[:,2], label=label[2])
        plt.plot(t, d[:,3], label=label[3])
        plt.plot(t, d[:,8], label=label[8])
        plt.savefig("{}_flow.jpg".format(tag))
        plt.xlabel("Time/s")
        plt.legend()
        plt.clf()
   



if __name__ == "__main__":
    sys.exit(main(sys.argv))
