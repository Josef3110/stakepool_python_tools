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

VERSION = "0.4"
NODE_NAME = "Cardano Node" 
REFRESH_RATE = 3

# define some default values upfront

METRICS_URL = "http://localhost:12788"
HEADERS = {'Accept': 'application/json'}
WIDTH = 72
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

#    style_title=${FG_MAGENTA}${BOLD}      # style of title
#    style_base=${FG_BLACK}                # default color for text and lines
#    style_values_1=${FG_BLUE}             # color of most live values
#    style_values_2=${FG_GREEN}            # color of node name
#    style_values_3=${STANDOUT}            # color of selected outgoing/incoming paging
#    style_values_4=${FG_LGRAY}               # color of informational text
#    style_info=${FG_YELLOW}               # info messages
#    style_status_1=${FG_GREEN}            # :)
#    style_status_2=${FG_YELLOW}           # :|
#    style_status_3=${FG_RED}              # :(
#    style_status_4=${FG_MAGENTA}          # :((
    
class bcolors:
        FG_BLACK = '\033[30m'
        FG_RED = '\033[31m'
        FG_GREEN = '\033[32m'
        FG_YELLOW = '\033[33m'
        FG_BLUE = '\033[34m'
        FG_MAGENTA = '\033[35m'
        FG_CYAN = '\033[36m'
        FG_LGRAY = '\033[37m'
        FG_DGRAY = '\033[90m'
        FG_LBLUE = '\033[94m'
        FG_WHITE = '\033[97m'
        STANDOUT = '\033[7m'
        BOLD = '\033[1m'
        NC = '\033[0m'    
    

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

topLine = DR
for i in range(0,WIDTH-2):
        if i == 33:
                topLine = topLine + DHL
        else:
                if i == 46:
                        topLine = topLine + DHL
                else:                        
                        topLine = topLine + HL
topLine = topLine + DL
line2 = VL + " ------------------------------- " + UR
for i in range(0,12):
        line2 = line2 + HL
line2 = line2 + UHL
for i in range(0,23):
        line2 = line2 + HL
line2 = line2 + UL
        
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

if args.config:
        parameter = get_parameter(args.config)
else:
        print("ERROR: path to config file required")
        sys.exit()

genesisFile = parameter["ShelleyGenesisFile"]
if parameter["EnableP2P"] == "true":
        p2p = "enabled"
else:
        p2p = "disabled"
        
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
density = round(float(metrics["cardano"]["node"]["metrics"]["density"]["real"]["val"]),3)
forks = metrics["cardano"]["node"]["metrics"]["forks"]["int"]["val"]
txsProcessedNum = metrics["cardano"]["node"]["metrics"]["txsProcessedNum"]["int"]["val"]
txsInMempool = metrics["cardano"]["node"]["metrics"]["txsInMempool"]["int"]["val"]
mempoolKBytes = round(int(metrics["cardano"]["node"]["metrics"]["mempoolBytes"]["int"]["val"])/1024,0)

peersCold = metrics["cardano"]["node"]["metrics"]["peerSelection"]["cold"]["val"]
peersWarm = metrics["cardano"]["node"]["metrics"]["peerSelection"]["warm"]["val"]
peersHot = metrics["cardano"]["node"]["metrics"]["peerSelection"]["hot"]["val"]

incomingConns = metrics["cardano"]["node"]["metrics"]["connectionManager"]["incomingConns"]["val"]
outgoingConns = metrics["cardano"]["node"]["metrics"]["connectionManager"]["outgoingConns"]["val"]
unidirectionalConns = metrics["cardano"]["node"]["metrics"]["connectionManager"]["unidirectionalConns"]["val"]
duplexConns = metrics["cardano"]["node"]["metrics"]["connectionManager"]["duplexConns"]["val"]
prunableConns = metrics["cardano"]["node"]["metrics"]["connectionManager"]["prunableConns"]["val"]

epochProgress = round(slotInEpoch/epochLength * 100,2)

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

print("\t> " + bcolors.FG_GREEN + NODE_NAME + bcolors.FG_BLACK + " - " + bcolors.FG_YELLOW +  "(" + nodeMode + " - " + networkId + ")" + bcolors.FG_BLACK + " : " + bcolors.FG_BLUE + nodeVersion + bcolors.FG_BLACK + " [" + bcolors.FG_BLUE + nodeRevision + bcolors.FG_BLACK + "] <")
print(topLine)
print(VL + " Uptime: " + "\t\t\t  " + VL + " Port: " + bcolors.FG_GREEN + nodePort + bcolors.FG_BLACK + " " + VL + bcolors.FG_MAGENTA + " ADAAT " + myname + " " + VERSION + " " + bcolors.FG_BLACK + VL)
print(line2)
print(VL + " Epoch " + str(epoch) + " [" + str(epochProgress) +"%], " + " remaining " + VL) 
print(VL + " Block      : " + str(blockNum) + "\tTip (ref)\t:" + "\tForks\t\t: " + str(forks) + " " + VL) 
print(VL + " Slot       : " + str(slotNum) + "\tTip (diff)\t:" + "\tTotal Tx\t: " + str(txsProcessedNum) + " " + VL)
print(VL + " Slot epoch : " + str(slotInEpoch) + "\tDensity\t: " + str(density) + "\tPending Tx : " + str(txsInMempool) + "/" + str(mempoolKBytes) + "K\t" + VL)
print(VL + " - CONNECTIONS -------------------------------------------------------- " + VL)
print(VL + " P2P        : " + p2p + "\tCold Peers : " + str(peersCold) + "\tUni-Dir    : " + str(unidirectionalConns) + "\t" + VL)
print(VL + " Incoming   : " + str(incomingConns) + "\tWarm Peers : " + str(peersWarm) + "\t Bi-Dir     :" + str(duplexConns) + "\t" + VL)
print(VL + " Outgoing   : " + str(outgoingConns) + "\tHot Peers  : " + str(peersHot) + "\tDuplex    : " + str(prunableConns) + "\t" + VL)
print(VL + " - BLOCK PROPAGATION -------------------------------------------------- " + VL)

