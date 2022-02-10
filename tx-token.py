#!/usr/bin/python3
#
# simple transaction

import os
import sys
import re
import subprocess
import argparse
import json
import base64

VERSION = "0.1"
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
    command = "cardano-cli transaction build-raw" + tx_in 
    command = command + " --tx-out " + dest
    command = command + " --tx-out " + src
    command = command + " --invalid-hereafter " + slot
    command = command + " --fee " + fee
    command = command + " --out-file tx.draft"
    if debug:
        print("DEBUG: " + str(command))
    p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,shell=True)
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
parser.add_argument("amount", metavar="amount", type=int, help="the amount tokens")
parser.add_argument("token", metavar="token name", type=str, help="the name of the token")
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

token_amount = args.amount
token_name = args.token
src = args.src_address
dest = args.dest_address

if args.testnet_magic:
    magic = ["--testnet-magic", str(args.testnet_magic)]
else:
    magic = ["--mainnet"]

token_enc = str(base64.b16encode(str.encode(token_name)).decode('utf8')).lower()

ignore = do_query("protocol-parameters","",magic,print_debug)
tip = json.loads(do_query("tip","",magic,print_debug))

if float(tip['syncProgress']) < 100.0:
    print("ERROR: node not in sync, please wait until sync process has been finished")
    sys.exit()

current_slot = int(tip['slot'])

all_utxo = do_query("utxo",src,magic,print_debug).splitlines()

# prepare for loop
ada_balance = 0
token_balance = 0
tx_count = 0
utxo_count = 2
tx_in = ""
token = []

while (ada_balance < (ADA2LOVELACE+FEE_THRESHOLD) or (token_balance < token_amount)):           # add tx_in until amount is available to save fees
    utxo = all_utxo[utxo_count]
    col = re.split(r'\s+',utxo)   
    if len(col) > 6:
        token = col[6].split('.')
        if token[1] == token_enc:
                ada_balance = ada_balance + int(col[2])
                token_balance = token_balance + int(col[5])
                tx_in = tx_in + " --tx-in " + col[0] + "#" + col[1]
                tx_count = tx_count + 1

    if (ada_balance < (ADA2LOVELACE+FEE_THRESHOLD)) and (len(col) <= 6):
        ada_balance = ada_balance + int(col[2])
        tx_in = tx_in + " --tx-in " + col[0] + "#" + col[1]
        tx_count = tx_count + 1
    utxo_count = utxo_count + 1

if len(token) == 0:
    print("ERROR: not enough " + token_name + " in src address")
    sys.exit()


oneADA = int(1.4*ADA2LOVELACE)
tx_out_dest = dest + '+' + str(oneADA) + '+"' + str(token_amount) + ' ' + token[0] + '.' + token[1] + '"'

ada_remaining = ada_balance - oneADA
token_remaining = token_balance - token_amount
tx_out_src = src + '+' + str(ada_remaining) + '+"' + str(token_remaining) + ' ' + token[0] + '.' + token[1] + '"'

ignore = do_transaction_raw(tx_in,tx_out_src,tx_out_dest,str(current_slot + 10000),"0",print_debug)
get_tx_fee = do_calculate_fee(str(tx_count),magic,print_debug)
fee = int(get_tx_fee.split(" ")[0])
ada_remaining = ada_balance - oneADA - fee
tx_out_src = src + '+' + str(ada_remaining) + '+"' + str(token_remaining) + ' ' + token[0] + '.' + token[1] + '"'


# feedback what's in the transaction
print("sending " + str(token_amount) + " " + token_name + " and 1 ADA and a fee of " + str(fee) + " lovelace")
print("from " + src)
print("to   " + dest)
if args.testnet_magic:
    print("on testnet with magic = " + str(args.testnet_magic))
else:
    print("on mainnet")

ignore = do_transaction_raw(tx_in,tx_out_src,tx_out_dest,str(current_slot + 10000),str(fee),print_debug)

