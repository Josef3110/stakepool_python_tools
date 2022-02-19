#!/usr/bin/python3
#
# sending current tip to pooltool.io

import os
import sys
import re
import subprocess
import argparse
import json
import requests
import time
from datetime import datetime

VERSION = "0.1"
PLATFORM = "sendtip.py by ADAAT"
URL = "https://api.pooltool.io/v0/sendstats"

def postPooltool(content):
    try:
        newHeaders = {'Content-type': 'application/json', 'Accept': 'Accept: application/json'}
        response = requests.post(URL, data=content, headers=newHeaders)
        requests.post(URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(ec, "Http Error: " + repr(errh))
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        print(ec,+ "Error Connecting: " + repr(errc))
        sys.exit()
    except requests.exceptions.Timeout as errt:
        print(ec, + "Timeout Error: " + repr(errt))
        sys.exit()
    except requests.exceptions.RequestException as err:
        print(ec, + "OOps: Something Else " + repr(err))
        sys.exit()
    finally:
        return response;

def getconfig(configfile):
    with open(configfile) as f:
        data = json.load(f)
    return data;

def do_query(magic,debug):
    command = ["cardano-cli", "query", "tip"]
    command = command + magic
    if debug:
        print("DEBUG: " + str(command))
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
    if (get_it[1] != ""):
        print("ERROR: " + get_it[1])
        sys.exit()
    else:
        return (get_it[0])

def get_node_version(magic,debug):
    command = ["cardano-node", "--version"]
    if debug:
        print("DEBUG: " + str(command))
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
    if (get_it[1] != ""):
        print("ERROR: " + get_it[1])
        sys.exit()
    else:
        return (get_it[0])


# main

# start with parsing arguments

parser = argparse.ArgumentParser(description="sendtip for pooltool.io")
parser.add_argument("-a", "--apiKey", type=str, nargs='?', help="API key from pooltool.io")
parser.add_argument("-p", "--poolId", type=str, nargs='?', help="pool ID")
parser.add_argument("-c", "--config", type=str, nargs='?', help="path to config file in json format", default="pooltool.json")
parser.add_argument("-t", "--testnet-magic", type=int, nargs='?', const=1097911063, help="run on testnet with magic number")
parser.add_argument("-d", "--debug", help="prints debugging information", action="store_true")
parser.add_argument("-v", "--version", action="version", version='%(prog)s Version ' + VERSION)
args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.debug:
    print("Debugging enabled")
    print_debug = True
else:
    print_debug = False

if args.testnet_magic:
    magic = ["--testnet-magic", str(args.testnet_magic)]
    magic_param = "--testnet-magic " + str(args.testnet_magic)
else:
    magic = ["--mainnet"]
    magic_param = "--mainnet"

#if args.config:
if not magic:
        my_config = getconfig(args.config)
else:        
        api_key = args.apiKey
        poolID = args.poolId

node_version = get_node_version(magic,print_debug).splitlines()
row1 = re.split(r'\s+',node_version[0])
row2 = re.split(r'\s+',node_version[1])
node_version = row1[1]
node_git = row2[2]


while True:
        tip = json.loads(do_query(magic,print_debug))
        message = {}
        message["apiKey"] = api_key
        message["poolId"] = poolID
        message["data"] = {}
        message["data"]["nodeId"] = ""
        message["data"]["version"] = node_version + ":" + node_git[:5]
        message["data"]["at"] = datetime.now().isoformat() + "Z"
        message["data"]["blockNo"] = tip["block"]
        message["data"]["slotNo"] = tip["slot"]
        message["data"]["blockHash"] = tip["hash"]
        message["data"]["platform"] = PLATFORM
#        print(json.dumps(message))
        response = postPooltool(json.dumps(message))
        print(response.json())
        time.sleep(15)

