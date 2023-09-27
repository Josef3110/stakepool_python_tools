#!/usr/bin/python3
#
# topologyUpdater as python variant

import os
import sys
import re
import subprocess
import argparse
import requests
import json
import time
from datetime import datetime

VERSION = "0.3"
NODE_NAME = "Cardano Node" 
REFRESH_RATE = 2

# define some default values upfront

METRICS_URL = "http://localhost:12788"
HEADERS = {'Accept': 'application/json'}
WIDTH = 70
MARKED = "\u258C"
UNMARKED = "\u2596"
VL = "\u2502"
HL = "\u2500"
LVL = "\u2524"
RVL = "\u251C"
UHL = "\u2534"
DHL = "\u252C"
UR = "\u2514"
UL = "\u2518"
DR = "\u250C"
DL = "\u2510"

#print(LVL + VL + RVL)
#print(UHL + HL + DHL)

def get_node_version(debug):
    command = ["cardano-node", "version"]        
    if debug:
        print("DEBUG: " + str(command))
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
    if (get_it[1] != ""):
        print("ERROR: " + get_it[1])
        sys.exit()
    else:
        return (get_it[0])

def timestamp4log():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S");

def get_parameter(sourceFile):
    with open(sourceFile) as f:
        data = json.load(f)
    return data;

def requestmetric(url):
    try:
        response = requests.get(url, headers = HEADERS)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        sys.exit()
    except requests.exceptions.Timeout as errt:
        sys.exit()
    except requests.exceptions.RequestException as err:
        sys.exit()
    finally:
        metrics = response.json()
        return metrics;

# main

completeLine = ""
for i in range(0,WIDTH):
        completeLine = completeLine + HL
        
#ec = {}
#sys.excepthook = exception_handler

# start with parsing arguments

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--version", help="displays version and exits", action="store_true")
parser.add_argument("-c", "--config", help="path to config file in json format", default="config.json")
parser.add_argument("-t", "--testnet-magic", type=int, nargs='?', const=1, help="run on preprod testnet with magic number")
parser.add_argument("-d", "--debug", help="prints debugging information", action="store_true")
parser.add_argument("-p", "--port", help="port number of the node", default="6000")

args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.version:
    print("ADAAT " + myname + " " + VERSION)
    sys.exit()

if args.debug:
    print("Debugging enabled")
    print_debug = True
else:
    print_debug = False
    
nodePort = args.port
parameter = get_parameter(args.config)

genesisFile = parameter["ShelleyGenesisFile"]
genesis = get_parameter(genesisFile)

networkId = genesis["networkId"]
networkMagic = genesis["networkMagic"]
systemStart = genesis["systemStart"]
epochLength = genesis["epochLength"]
slotLength = genesis["slotLength"]
activeSlotsCoeff = genesis["activeSlotsCoeff"]

#if args.config:
#    my_config = getconfig(args.config)
#    if 'hostname' in my_config:
#        cnode_hostname = my_config['hostname']
#    else:
#        sys.exit()
#    if 'port' in my_config:
#        cnode_port = my_config['port']
#    else:
#        sys.exit()
#    if 'networkMagic' in my_config:
#        nwmagic = my_config['networkMagic']
#    else:
#        nwmagic = nwmagic_default

# start cardano-node binary to get version and revision number
nodeInfo = get_node_version(print_debug)
nodeInfoLines = nodeInfo.splitlines()
nodeInfoLine1 = re.split(r'\s+',nodeInfoLines[0])
nodeInfoLine2 = re.split(r'\s+',nodeInfoLines[1])
nodeVersion = nodeInfoLine1[1]
nodeRevision = nodeInfoLine2[2][:8]

# get metrics in JSON via EKG
metrics = requestmetric(METRICS_URL)
#print(response.encoding)

epoch = metrics["cardano"]["node"]["metrics"]["epoch"]["int"]["val"]
blockNum = metrics["cardano"]["node"]["metrics"]["blockNum"]["int"]["val"]
slotInEpoch = metrics["cardano"]["node"]["metrics"]["slotInEpoch"]["int"]["val"]
slotNum = metrics["cardano"]["node"]["metrics"]["slotNum"]["int"]["val"]
density = metrics["cardano"]["node"]["metrics"]["density"]["real"]["val"]
forks = metrics["cardano"]["node"]["metrics"]["forks"]["int"]["val"]
txsProcessedNum = metrics["cardano"]["node"]["metrics"]["txsProcessedNum"]["int"]["val"]
txsInMempool = metrics["cardano"]["node"]["metrics"]["txsInMempool"]["int"]["val"]
mempoolBytes = metrics["cardano"]["node"]["metrics"]["mempoolBytes"]["int"]["val"]

#response_list = response.text.splitlines(True)
#metrics = {}
#for element in response_list:
#        metric = element.rstrip('\n').split()
#        metrics[metric[0]] = metric[1]

#block_number = metrics['cardano_node_metrics_blockNum_int']

aboutToLead = 0
if aboutToLead == 0:
        nodeMode = "Relay"
else:
        nodeMode = "Core"

print("\t> " + NODE_NAME + " - (" + nodeMode + " - " + networkId + ") : " + nodeVersion + " [" + nodeRevision + "] <")
print(completeLine)
print(VL + " Uptime: " + "\t\t\t" + VL + " Port: " + nodePort + " " + VL + " ADAAT " + myname + " " + VERSION + " " + VL)
print(VL + " Epoch " + str(epoch) + " [" + "], " + " remaining")
print(VL + " Block\t: " + str(blockNum) + "\tTip (ref)\t:" + "\tForks\t\t: " + str(forks))
print(VL + " Slot\t: " + str(slotNum) + "\tTip (diff)\t:" + "\tTotal Tx\t: " + str(txsProcessedNum))
