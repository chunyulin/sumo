#!/usr/bin/env python

"""
Given a net.xml with customized indirect-turn connections with linkIndex2 set,
the code adjust the start/end point of customized connections to be that of the incoming/outgoint lane point,
and calculate the suiable contPos.  
"""

from __future__ import absolute_import
from __future__ import print_function

import numpy as np
import optparse
from sumolib import checkBinary  # noqa

#from io import StringIO
#from xml.dom import pulldom
#from xml.dom import Node
from optparse import OptionParser
#from subprocess import call
#from collections import defaultdict

import xml.etree.ElementTree as ET
#import copy
import re


def operation(node):
    if node.tag == "connection":
        a = node.attrib
        if 'contPos' in a.keys():
            print(a['linkIndex'], a['linkIndex2'], a['contPos'])
            a['contPos'] = "999.00"
    
def recur_node(node, f):
    if node != None:
        f(node)
        for item in node:
            recur_node(item, f)
    else:
        return 0

def str2coor(str):    
    return [ float(x) for x in re.split(' |,', str) ]
def coor2str(coor):
    str = []
    for i in range(0,len(coor),2):
       str.append("{},{}".format(coor[i],coor[i+1]) ) 
    return ' '.join(str)
def calContPos(c):
    d = 0.0
    for i in range(0,len(c)-4,2):
        d += np.sqrt( (c[i+2]-c[i])**2 + (c[i+3]-c[i+1])**2  ) 
    return d
       
def modifyIndirectLeftTurnConnection(tree):
    root = tree.getroot()

    for conn in root.iter('connection'):   
        a = conn.attrib
        #print(a['linkIndex'], a['linkIndex2'], a['contPos'], a['fromLane'], a['toLane'])
        # get all left-turn motor connection
        if 'linkIndex2' in a.keys() and a['dir'] == "l" and a['fromLane'] == '0':  ##'contPos' in a.keys() and 
            lane0id = "{}_{}".format(a['from'],a['fromLane'])
            lane1id = "{}_{}".format(a['to'],a['toLane'])
        
            ## start/end lane. May not usful
            lane0 = root.findall('./edge/lane[@id=\"{}\"]'.format(lane0id))  # source
            lane1 = root.findall('./edge/lane[@id=\"{}\"]'.format(lane1id))  # target
            p0 = [ float(x) for x in lane0[0].attrib['shape'].split(' ')[-1].split(',') ]
            p1 = [ float(x) for x in lane1[0].attrib['shape'].split(' ')[ 0].split(',') ]
        
            shape = str2coor(a['shape'])
            print("Source: ", a['shape'])
            shape[:2]  = p0[0], p0[1]
            shape[-2:] = p1[0], p1[1]
            a['shape']   = coor2str(shape)
            a['contPos'] = str( calContPos(shape) )
            print("Target: ", a['shape'])
        
        
def main(args=None):
    optParser = OptionParser()
    optParser.add_option("-i", "--input", dest="input", metavar="FILE",
                         help="Defines the input file to use")
    optParser.add_option("-o", "--output", dest="output", metavar="FILE", default="output.net.xml")
    options, args = optParser.parse_args()
 
    tree = ET.parse(options.input)
    root = tree.getroot()
    modifyIndirectLeftTurnConnection(tree)

    
    tree.write(options.output)
    
        
if __name__ == "__main__":
  main()