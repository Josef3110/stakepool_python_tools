#!/usr/bin/python3
#
# simple transaction

import os
import sys
import re
import subprocess
import argparse
import json

VERSION = "0.7"
ADA2LOVELACE = 1000000
FEE_THRESHOLD = int(0.2 * ADA2LOVELACE)

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
    command.append(src)
    command.append("--tx-out")
    command.append(dest)
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
parser.add_argument("-v", "--version", action="version", version='%(prog)s Version ' + VERSION)
args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.debug:
    print("Debugging enabled")
    print_debug = True
else:
    print_debug = False

amount = int(args.amount * ADA2LOVELACE)
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

all_utxo = do_query("utxo",src,magic,print_debug).splitlines()

# prepare for loop
balance = 0
tx_in = ""
tx_count = 0
tx_in = []

while balance < (amount+FEE_THRESHOLD):           # add tx_in until amount is available to save fees
    utxo = all_utxo[tx_count+2]
    col = re.split(r'\s+',utxo)
    balance = balance + int(col[2])
    tx_in.append("--tx-in")
    tx_in.append(col[0] + "#" + col[1])
    tx_count = tx_count + 1

ignore = do_transaction_raw(tx_in,src + "+0",dest + "+0",str(current_slot + 10000),"0",print_debug)
get_tx_fee = do_calculate_fee(str(tx_count),magic,print_debug)
fee = int(get_tx_fee.split(" ")[0])
tx_out = balance - fee - amount

# feedback what's in the transaction
print("sending " + str(amount) + " lovelace and a fee of " + str(fee) + " lovelace")
print("from " + src)
print("to   " + dest)
if args.testnet_magic:
    print("on testnet with magic = " + str(args.testnet_magic))
else:
    print("on mainnet")

ignore = do_transaction_raw(tx_in,src + "+" + str(tx_out),dest + "+" + str(amount),str(current_slot + 10000),str(fee),print_debug)
