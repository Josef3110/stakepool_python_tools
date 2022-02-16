#!/usr/bin/python3
#
# query balance of an address

import os
import sys
import re
import subprocess
import argparse
import json
import base64

version = "0.6"
ada2lovelace = 1000000

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

parser = argparse.ArgumentParser(description="query balance for a given address")
parser.add_argument("address", type=str, help="the address")
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
amount_ada = 0
token_value = 0
token = {}

for utxo in all_utxo:
    if (skip_header < 2):
        skip_header = skip_header + 1
    else:
        col = re.split(r'\s+',utxo)
        amount_ada = amount_ada + int(col[2])
        number_of_token = int((len(col) - 5)/3)
        i = 5
        while i < (len(col)-2):
                token_utxo = col[i+1].split('.')
                token_name = token_utxo[1]
                token_dec = str(base64.b16decode(token_name.encode('utf8').upper()).decode('utf8'))
                token_amount = int(col[i])
                if token_dec in token:
                        token[token_dec] = token[token_dec] + token_amount
                else:
                        token[token_dec] = token_amount
                i = i + 3

print("balance is " + str(float(amount_ada)/ada2lovelace) + " ADA")
if token:
        print("balance of token (without digits):")
        for token_item in token.keys():
                print("\t" + str(token[token_item]) + " " + token_item)

if print_debug:
    if args.testnet_magic:
        print("on testnet with magic = " + str(args.testnet_magic))
    else:
        print("on mainnet")
