#!/usr/bin/python3
#
# simple transaction

import os
import sys
import re
import subprocess
import argparse
import json
import time
from datetime import datetime

version = "0.4"

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

def do_transaction_raw(tx_in,src,dest,slot,fee,debug):
    command = ["cardano-cli", "transaction", "build-raw"] + tx_in
    command.append("--tx-out")
    command.append(src + "+0")
    command.append("--tx-out")
    command.append(dest + "+0")
    command.append("--invalid-hereafter")
    command.append(slot)
    command.append("--fee")
    command.append(fee)
    command.append("--out-file")
    command.append("tx.draft")
    if debug:
        print("DEBUG: " + str(command))
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
    if (get_it[1] != ""):
        print("ERROR: " + get_it[1])
        sys.exit()
    else:
        return (get_it[0])

def do_calculate_fee(count,magic,debug):
    command = ["cardano-cli", "transaction", "calculate-min-fee"]
    command.append("--tx-body-file")
    command.append("tx.draft")
    command.append("--tx-in-count")
    command.append(count)
    command.append("--tx-out-count")
    command.append("2")
    command.append("--witness-count")
    command.append("1")
    command.append("--byron-witness-count")
    command.append("0") 
    command.append("--protocol-params-file")
    command.append("params.json")
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

parser = argparse.ArgumentParser(description="build a transaction for signing with your keys")
parser.add_argument("amount", metavar="amount", type=float, help="the amount of the transaction in ADA")
parser.add_argument("src_address", metavar="source", type=str, help="the source address")
parser.add_argument("dest_address", metavar="destination", type=str, help="the destination address")
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

amount = int(args.amount * 1000000)
src = args.src_address
dest = args.dest_address

if args.testnet_magic:
    magic = ["--testnet-magic", str(args.testnet_magic)]
else:
    magic = ["--mainnet"]

ignore = do_query("protocol-parameters","",magic,print_debug)
tip = json.loads(do_query("tip","",magic,print_debug))

if float(tip['syncProgress']) < 100.0:
    print("ERROR: node not in sync, please wait until sync process has been finished")
    sys.exit()

current_slot = int(tip['slot'])
print("sending " + str(amount) + " lovelace")
print("from " + src)
print("to   " + dest)
if args.testnet_magic:
    print("on testnet with magic = " + str(args.testnet_magic))
else:
    print("on mainnet")

all_utxo = do_query("utxo",src,magic,print_debug).splitlines()
skip_header = 0
src_amount = 0
tx_in = ""
tx_count = 0

tx_in = []
for utxo in all_utxo:
    if (skip_header < 2):
        skip_header = skip_header + 1
    else:
        col = re.split(r'\s+',utxo)
        src_amount = src_amount + int(col[2])
        tx_in.append("--tx-in")
        tx_in.append(col[0] + "#" + col[1])
        tx_count = tx_count + 1

ignore = do_transaction_raw(tx_in,src,dest,str(current_slot + 10000),"0",print_debug)
get_tx_fee = do_calculate_fee(str(tx_count),magic,print_debug)
fee = int(get_tx_fee.split(" ")[0])
print(fee)
tx_out = src_amount - fee - amount
print(amount)
print(tx_out)

ignore = do_transaction_raw(tx_in,src,dest,str(current_slot + 10000),str(fee),print_debug)
