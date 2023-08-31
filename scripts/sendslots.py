#!/usr/bin/python3
#
# sending slots for current epoch to pooltool.io (must be in the first 60 minutes of the current epoch)

import os
import sys
import re
import subprocess
import argparse
import json
import requests
import hashlib
import time
from datetime import datetime

VERSION = "0.7"
PLATFORM = "sendslots.py by ADAAT"
URL = "https://api.pooltool.io/v0/sendslots"

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
    
def writeconfig(configfile,configjson):
    with open(configfile, 'w') as f:
        f.write(json.dumps(configjson,indent=4))
    return 0;

def parse_query(leader):
    slot_list = []
#    print(leader)
    all_leader = leader.splitlines()
    skip_header = 0    
    for leader_line in all_leader:
        if (skip_header < 2):
                skip_header = skip_header + 1
        else:
                col = re.split(r'\s+',leader_line)
                slot_list.append(int(col[1]))
    return slot_list;

def do_query(what,config,magic,debug):
    command = ["cardano-cli", "query", what]
    if (what == "leadership-schedule"):
        command.append("--genesis")
        command.append(config['genesis_file'])
        command.append("--stake-pool-id")
        command.append(config['pools'][0]['pool_id'])
        command.append("--vrf-signing-key-file")
        command.append(config['key_file'])
        command.append("--current")
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

# main

# start with parsing arguments

parser = argparse.ArgumentParser(description="sendtip for pooltool.io")
parser.add_argument("-c", "--config", type=str, nargs='?', help="path to config file in json format")
parser.add_argument("-t", "--testnet-magic", type=int, nargs='?', const=1, help="run on preprod testnet with magic number")
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

if args.config:
        my_config = getconfig(args.config)
        api_key = my_config['api_key']
        poolID = my_config['pools'][0]['pool_id']
        genesis_file = my_config['genesis_file']
        key_file = my_config['key_file']
else:        
        print("ERROR: please provide a config file!")
        
last_block = ""
prev_block_hash = ""

if print_debug:
        print("sendslots is configured with:")
        print("\tAPI key " + api_key)
        print("\tpool ID " + poolID )
        print("\tgenesis file " + genesis_file)
        print("\tkey file " + key_file)
        print("\tsaved_data " + str(my_config['saved_data']))

tip = json.loads(do_query("tip",{},magic,print_debug))
if float(tip['syncProgress']) < 100.0:
        print("ERROR: node not in sync, please wait until sync process has been finished")
        sys.exit()
 
epoch = tip['epoch']
epoch1 = my_config['saved_data'][0]['epoch']
epoch2 = my_config['saved_data'][1]['epoch']

if ((epoch-1) > epoch1):
        my_config['saved_data'][0]['epoch'] = epoch - 1
        if (epoch2 == (epoch-1)):
                my_config['saved_data'][0]['slots'] = my_config['saved_data'][1]['slots']
        else:                
                my_config['saved_data'][0]['slots'] = []
if (epoch > epoch2):
        leader = do_query("leadership-schedule",my_config,magic,print_debug)
        slot_list = parse_query(leader)
        if print_debug:
                print("DEBUG: current list of slots " + str(slot_list))
        my_config['saved_data'][1]['epoch'] = epoch
        my_config['saved_data'][1]['slots'] = slot_list
print("saving new data back to config file")
writeconfig(args.config,my_config)
        
message = {}
message["apiKey"] = api_key
message["poolId"] = poolID
message["epoch"] = epoch
message["slotQty"] = len(my_config['saved_data'][1]['slots'])
slotsstring = json.dumps(my_config['saved_data'][1]['slots'],separators=(',', ':'))
## code snipet provided by papacarp from pooltool.io
h=hashlib.blake2b(digest_size=32)
h.update(slotsstring.encode())
hresult=h.hexdigest()
##
message["hash"] = str(hresult)
message["prevSlots"] = json.dumps(my_config['saved_data'][0]['slots'],separators=(',', ':'))
if print_debug:
        print(json.dumps(message))
response = postPooltool(json.dumps(message))
if print_debug:
        print("pooltool.io response: " + str(response.json()))

