#!/usr/bin/python3
#
# query balance of an address

import os
import sys
import re
import subprocess
import argparse
import json

version = "0.1"

def do_query(what,parameter,magic,debug):
    if (what == "tip"):
        command = ["cardano-cli", "query", what]
    if (what == "protocol-parameters"):
        command = ["cardano-cli", "query", what, "--out-file", "params.json"]
    if (what == "utxo"):
        command = ["cardano-cli", "query", what, "--address"]
        command.append(parameter)
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

parser = argparse.ArgumentParser(description="query balance for a given wallet address")
parser.add_argument("address", type=str, help="the wallet address")
parser.add_argument("-t", "--testnet-magic", type=int, nargs='?', const=1097911063, help="run on testnet with magic number")
parser.add_argument("-d", "--debug", help="prints debugging information", action="store_true")
parser.add_argument("-v", "--version", action="version", version='%(prog)s Version ' + version)
args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.debug:
    print("Debugging enabled")
    print_debug = True
else:
    print_debug = False

address = args.address

if args.testnet_magic:
    magic = ["--testnet-magic", str(args.testnet_magic)]
else:
    magic = ["--mainnet"]

tip = json.loads(do_query("tip","",magic,print_debug))

if float(tip['syncProgress']) < 100.0:
    print("ERROR: node not in sync, please wait until sync process has been finished")
    sys.exit()


all_utxo = do_query("utxo",address,magic,print_debug).splitlines()
skip_header = 0
amount = 0

for utxo in all_utxo:
    if (skip_header < 2):
        skip_header = skip_header + 1
    else:
        col = re.split(r'\s+',utxo)
        amount = amount + int(col[2])

print("balance of " + address + " is " + str(float(amount)/1000000))
if args.testnet_magic:
    print("on testnet with magic = " + str(args.testnet_magic))
else:
    print("on mainnet")
