from __future__ import absolute_import
from __future__ import print_function

import os
import sys

sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import sumolib  # noqa
from sumolib.visualization import helpers  # noqa
import matplotlib.pyplot as plt  # noqa
import numpy as np

def main(args=None):
    """The main function; parses options and plots"""
    # ---------- build and read options ----------
    from optparse import OptionParser
    optParser = OptionParser()
    optParser.add_option("-i", "--summary-inputs", dest="summary", metavar="FILE",
                         help="Defines the summary-output files to use as input")
    helpers.addInteractionOptions(optParser)
    #helpers.addPlotOptions(optParser)
    options, _ = optParser.parse_args(args=args)

    #<step time="0.50" loaded="24" inserted="23" running="23" waiting="1" ended="0" arrived="0" collisions="0" teleports="0" halting="0" stopped="0" #meanWaitingTime="0.07" meanTravelTime="-1.00" meanSpeed="17.18" meanSpeedRelative="0.89" duration="368879895"/>
    
    if options.summary is None:
        print("Error: at least one summary file must be given")
        sys.exit(1)

    files = options.summary.split(",")
    
    cols = ["time", "loaded", "inserted", "running", "ended", 
            "arrived", "collisions", "teleports", "halting", "stopped", 
            "meanWaitingTime", "meanTravelTime", "meanSpeed", "meanSpeedRelative"]
    
    d = []
    for data in sumolib.xml.parse_fast(files[0], "step", cols):
        d.append([float(x) for x in data])
    d = np.array(d)    
    t = d[:,0]

    plt.figure()
    
    plt.clf()
    plt.plot(t, d[:,3], label=cols[3])
    plt.plot(t, d[:,8], label=cols[8])
    plt.plot(t, d[:,9], label=cols[9])
    plt.plot(t, d[:,6], label=cols[6])
    plt.plot(t, d[:,7], label=cols[7])
    plt.xlabel("Time/s")
    plt.legend()
    plt.savefig("summ_number.jpg")
    
    plt.clf()
    plt.plot(t, d[:,10], label=cols[10])
    plt.plot(t, d[:,11], label=cols[11])
    plt.plot(t, d[:,12], label=cols[12])
    plt.xlabel("Time/s")
    plt.legend()
    plt.savefig("summ_time.jpg")
    


if __name__ == "__main__":
    sys.exit(main(sys.argv))
