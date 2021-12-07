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

version = "0.2"

def do_query(what,parameter):
    if (what == "tip"):
        command = ["cardano-cli", "query", what, "--mainnet"]
    if (what == "protocol-parameters"):
        command = ["cardano-cli", "query", what, "--mainnet", "--out-file", "params.json"]
    if (what == "utxo"):
        command = ["cardano-cli", "query", what, "--address"]
        command.append(parameter)
        command.append("--mainnet")
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
#    if (get_it[1] == ""):
#        print(get_it[1])
#        sys.exit()
#    else:
    return (get_it[0])

def do_transaction_raw(tx_in,src,dest,slot,fee,out):
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
    command.append(out)
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
#    if (get_it[1] == ""):
#        print(get_it[1])
#        sys.exit()
#    else:
    return (get_it[0])

def do_calculate_fee(count):
    command = ["cardano-cli", "transaction", "calculate-min-fee"]
    command.append("--tx-body-file")
    command.append("tx.tmp")
    command.append("--tx-in-count")
    command.append(count)
    command.append("--tx-out-count")
    command.append("2")
    command.append("--mainnet")
    command.append("--witness-count")
    command.append("1")
    command.append("--byron-witness-count")
    command.append("0") 
    command.append("--protocol-params-file")
    command.append("params.json")
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    get_it = p.communicate()
#    if (get_it[1] == ""):
#        print(get_it[1])
#        sys.exit()
#    else:
    return (get_it[0])


# main

# start with parsing arguments

parser = argparse.ArgumentParser()
parser.add_argument("amount", metavar = "amount", type=float, help="the amount of the transaction in ADA")
parser.add_argument("src_address", metavar = "source", type=str, help="the source address")
parser.add_argument("dest_address", metavar = "destination", type=str, help="the destination address")
parser.add_argument("-v", "--version", help="displays version and exits", action="store_true")
args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.version:
    print(myname + " version " + version)
    sys.exit()

amount = int(args.amount * 1000000)
src = args.src_address
dest = args.dest_address

ignore = do_query("protocol-parameters","")
tip = json.loads(do_query("tip",""))

if float(tip['syncProgress']) < 100.0:
    print("node not in sync, please wait until sync process has been finished")
    sys.exit()

current_slot = int(tip['slot'])
print("sending " + str(amount) + " lovelace")
print("from " + src)
print("to   " + dest)

all_utxo = do_query("utxo",src).splitlines()
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
        tx_in.append(col[0] + "#0")
        tx_count = tx_count + 1

ignore = do_transaction_raw(tx_in,src,dest,str(current_slot + 10000),"0","tx.tmp")
get_tx_fee = do_calculate_fee(str(tx_count))
fee = int(get_tx_fee.split(" ")[0])
print(fee)
tx_out = src_amount - fee - amount
print(amount)
print(tx_out)

ignore = do_transaction_raw(tx_in,src,dest,str(current_slot + 10000),str(fee),"tx.raw")
