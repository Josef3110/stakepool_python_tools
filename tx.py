#!/usr/bin/python3
#
# simple transaction

import os
import sys
import re
import subprocess
import argparse
import requests
import json
import time
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from datetime import datetime

version = "0.1"

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

p = subprocess.Popen(["cardano-cli", "query", "tip", "--mainnet"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
get_current_slot = p.communicate()
tip = json.loads(get_current_slot[0])

if float(tip['syncProgress']) < 100.0:
    print("node not in sync, please wait until sync process has been finished")
    sys.exit()

current_slot = int(tip['slot'])
print("sending " + str(amount) + " lovelace")
print("from " + src)
print("to   " + dest)

command = ["cardano-cli", "query", "utxo", "--address"]
command.append(src)
command.append("--mainnet")
p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
get_all_utxo = p.communicate()
all_utxo = get_all_utxo[0].splitlines()
skip_header = 0
src_amount = 0
tx_in = ""
tx_count = 0

command = ["cardano-cli", "transaction", "build-raw"]
for utxo in all_utxo:
    if (skip_header < 2):
        skip_header = skip_header + 1
    else:
        col = re.split(r'\s+',utxo)
        src_amount = src_amount + int(col[2])
        command.append("--tx-in")
        command.append(col[0] + "#0")
        tx_count = tx_count + 1

command_raw = command.copy()
command.append("--tx-out")
command.append(src + "+0")
command.append("--tx-out")
command.append(dest + "+0")
command.append("--invalid-hereafter")
command.append(str(current_slot + 10000))
command.append("--fee")
command.append("0")
command.append("--out-file")
command.append("tx.tmp")
#print(command)

p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
get_tx_raw = p.communicate()
#print(get_tx_raw)

command = ["cardano-cli", "transaction", "calculate-min-fee"]
command.append("--tx-body-file")
command.append("tx.tmp")
command.append("--tx-in-count")
command.append(str(tx_count))
command.append("--tx-out-count")
command.append("2")
command.append("--mainnet")
command.append("--witness-count")
command.append("1")
command.append("--byron-witness-count")
command.append("0") 
command.append("--protocol-params-file")
command.append("params.json")
#print(command)
p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
get_tx_fee = p.communicate()
#print(get_tx_fee[0])
fee = int(get_tx_fee[0].split(" ")[0])
print(fee)
tx_out = src_amount - fee - amount
print(amount)
print(tx_out)

command_raw.append("--tx-out")
command_raw.append(src + "+" + str(tx_out))
command_raw.append("--tx-out")
command_raw.append(dest + "+" + str(amount))
command_raw.append("--invalid-hereafter")
command_raw.append(str(current_slot + 10000))
command_raw.append("--fee")
command_raw.append(str(fee))
command_raw.append("--out-file")
command_raw.append("tx.raw")
print(command_raw)
p = subprocess.Popen(command_raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
get_tx_raw = p.communicate()
print(get_tx_raw[0])
