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
import psutil
from datetime import datetime

VERSION = "0.6"
NODE_NAME = "Cardano Node"
PROC_NAME = "cardano-node" 
REFRESH_RATE = 2

# define some default values upfront

METRICS_URL = "http://localhost:12788"
HEADERS = {'Accept': 'application/json'}
WIDTH = 74
GRANULARITY = WIDTH - 4
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

# global variables for exit, help, etc.    
currentMode = "h"       # 'h' ... home, 'q' ... quit, 'i' ... info, 'p' ... peers


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
    
def time_left(seconds):
        days = int(round(seconds/60/60/24,0))
        hours = int(round(seconds/60/60%24,0))
        minutes = int(round(seconds/60%60,0))
        if days > 0:
                daysstr = str(days) + "d "
        else:
                daysstr = ""
        if hours < 10:
                hoursstr = "0" + str(hours)
        else:
                hoursstr = str(hours)
        if minutes < 10:
                minutesstr = "0" + str(minutes)
        else:
                minutesstr = str(minutes)
        if int(round(seconds%60,0)) < 10:
                secondesstr = "0" + str(int(round(seconds%60,0)))
        else:
                secondesstr = str(int(round(seconds%60,0)))
        return daysstr + hoursstr + ":" + minutesstr + ":" + secondesstr

def get_uptime(procname):
        for proc in psutil.process_iter():
                if proc.name() == procname:
                        etime = time.time() - proc.create_time()
        return etime

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
        if i == 35:
                topLine = topLine + DHL
        else:
                if i == 48:
                        topLine = topLine + DHL
                else:                        
                        topLine = topLine + HL
topLine = topLine + DL
emptyLine = VL
for i in range(0,WIDTH-2):
        emptyLine = emptyLine + " "
emptyLine = emptyLine + VL
line2 = VL + " --------------------------------- " + UR
for i in range(0,12):
        line2 = line2 + HL
line2 = line2 + UHL
for i in range(0,23):
        line2 = line2 + HL
line2 = line2 + LVL
lastLine = UR
for i in range(0,WIDTH-2):
        lastLine = lastLine + HL
lastLine = lastLine + UL
        
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
if bool(parameter["EnableP2P"]):
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


# start cardano-node binary to get version and revision number
nodeInfo = get_node_version(print_debug)
nodeInfoLines = nodeInfo.splitlines()
nodeInfoLine1 = re.split(r'\s+',nodeInfoLines[0])
nodeInfoLine2 = re.split(r'\s+',nodeInfoLines[1])
nodeVersion = nodeInfoLine1[1]
nodeRevision = nodeInfoLine2[2][:8]

# get metrics in JSON via EKG
while True:
        os.system('clear')
        metrics = requestmetric(METRICS_URL)

        epoch = metrics["cardano"]["node"]["metrics"]["epoch"]["int"]["val"]

        blockNum = metrics["cardano"]["node"]["metrics"]["blockNum"]["int"]["val"]
        slotInEpoch = metrics["cardano"]["node"]["metrics"]["slotInEpoch"]["int"]["val"]
        slotNum = metrics["cardano"]["node"]["metrics"]["slotNum"]["int"]["val"]
        density = round(float(metrics["cardano"]["node"]["metrics"]["density"]["real"]["val"])*100,3)
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

        lastDelay = round(float(metrics["cardano"]["node"]["metrics"]["blockfetchclient"]["blockdelay"]["s"]["val"]),2)
        served = metrics["cardano"]["node"]["metrics"]["served"]["block"]["count"]["int"]["val"]
        late = metrics["cardano"]["node"]["metrics"]["blockfetchclient"]["lateblocks"]["val"]
        cdfOne = round(float(metrics["cardano"]["node"]["metrics"]["blockfetchclient"]["blockdelay"]["cdfOne"]["val"]),2)
        cdfThree = round(float(metrics["cardano"]["node"]["metrics"]["blockfetchclient"]["blockdelay"]["cdfThree"]["val"]),2)
        cdfFive = round(float(metrics["cardano"]["node"]["metrics"]["blockfetchclient"]["blockdelay"]["cdfFive"]["val"]),2)
               
        epochProgress = round(slotInEpoch/epochLength * 100,2)
        epochItems = epochProgress * GRANULARITY/100
        epochBar = bcolors.FG_BLUE
        epochBarColor = epochBar
        for i in range(0,GRANULARITY):
                if i < epochItems:
                        epochBar = epochBar + MARKED
                else:
                        epochBar = epochBar + bcolors.FG_BLACK + UNMARKED
                        
        aboutToLead = 0
        if aboutToLead == 0:
                nodeMode = "Relay"
        else:
                nodeMode = "Core"

        print("\t> " + bcolors.FG_GREEN + NODE_NAME + bcolors.FG_BLACK + " - " + bcolors.FG_YELLOW +  "(" + nodeMode + " - " + networkId + ")" + bcolors.FG_BLACK + " : " + bcolors.FG_BLUE + nodeVersion + bcolors.FG_BLACK + " [" + bcolors.FG_BLUE + nodeRevision + bcolors.FG_BLACK + "] <")
        print(topLine)
        print(VL + " Uptime: " + bcolors.FG_BLUE  + time_left(get_uptime(PROC_NAME)) + bcolors.FG_BLACK + "\t\t    " + VL + " Port: " + bcolors.FG_GREEN + nodePort + bcolors.FG_BLACK + " " + VL + bcolors.FG_MAGENTA + " ADAAT " + myname + " " + VERSION + " " + bcolors.FG_BLACK + VL)
        print(line2)
        print(VL + " Epoch " + bcolors.FG_BLUE + str(epoch) + bcolors.FG_BLACK + " [" + bcolors.FG_BLUE + str(epochProgress) +"%" + bcolors.FG_BLACK + "], " + " remaining " + "\t" + VL)
        print(VL + " " +  epochBar + bcolors.FG_BLACK + " " + VL)
        print(emptyLine)        
        print(VL + " Block      : " + bcolors.FG_BLUE + str(blockNum) + bcolors.FG_BLACK + "\t Tip (ref)\t:" + "\tForks      : " + bcolors.FG_BLUE + str(forks) + bcolors.FG_BLACK + "\t " + VL) 
        print(VL + " Slot       : " + bcolors.FG_BLUE + str(slotNum) + bcolors.FG_BLACK + " Tip (diff)\t:" + "\tTotal Tx   : " + bcolors.FG_BLUE + str(txsProcessedNum) + bcolors.FG_BLACK + "\t " + VL)
        print(VL + " Slot epoch : " + bcolors.FG_BLUE + str(slotInEpoch) + bcolors.FG_BLACK + "\t Density\t: " + bcolors.FG_BLUE + str(density) + bcolors.FG_BLACK + "\tPending Tx : " + bcolors.FG_BLUE + str(txsInMempool) + bcolors.FG_BLACK + "/" + bcolors.FG_BLUE + str(mempoolKBytes) + bcolors.FG_BLACK + "K\t " + VL)
        print(VL + " - CONNECTIONS -------------------------------------------------------- " + VL)
        print(VL + " P2P        : " + bcolors.FG_YELLOW + p2p + bcolors.FG_BLACK + "\t Cold Peers : " + bcolors.FG_BLUE + str(peersCold) + bcolors.FG_BLACK + "\tUni-Dir    : " + bcolors.FG_BLUE + str(unidirectionalConns) + bcolors.FG_BLACK + "\t\t " + VL)
        print(VL + " Incoming   : " + bcolors.FG_BLUE + str(incomingConns) + bcolors.FG_BLACK + "\t Warm Peers : " + bcolors.FG_BLUE + str(peersWarm) + bcolors.FG_BLACK + "\tBi-Dir     : " + bcolors.FG_BLUE + str(duplexConns) + bcolors.FG_BLACK + "\t\t " + VL)
        print(VL + " Outgoing   : " + bcolors.FG_BLUE + str(outgoingConns) + bcolors.FG_BLACK + "\t Hot Peers  : " + bcolors.FG_BLUE + str(peersHot) + bcolors.FG_BLACK + "\tDuplex     : " + bcolors.FG_BLUE + str(prunableConns) + bcolors.FG_BLACK + "\t\t " + VL)
        print(VL + " - BLOCK PROPAGATION -------------------------------------------------- " + VL)
        print(VL + " Last Delay : " + bcolors.FG_BLUE + str(lastDelay) + bcolors.FG_BLACK + "s\t Served     : " + bcolors.FG_BLUE + str(served) + bcolors.FG_BLACK + "\tLate (>5s) : " + bcolors.FG_BLUE + str(late) + bcolors.FG_BLACK + "\t " + VL)
        print(VL + " Within 1s  : " + bcolors.FG_BLUE + str(cdfOne) + bcolors.FG_BLACK + "%\t Within 3s  : " + bcolors.FG_BLUE + str(cdfThree) + bcolors.FG_BLACK + "%\tWithin 5s  : " + bcolors.FG_BLUE + str(cdfFive) + bcolors.FG_BLACK + "%\t " + VL)
        print(VL + " - NODE RESOURCE USAGE ------------------------------------------------ " + VL)
        print(VL + " CPU (sys)  : " + "\t Mem (Live) : " + "\t GC Minor   : " + "\t " + VL)
        print(VL + " Mem (RSS)  : " + "\t Mem (Heap) : " + "\t GC Major   : " + "\t " + VL)
        print(lastLine)
        
        time.sleep(REFRESH_RATE)

