#!/usr/bin/python3
#
# simple transaction

import os
import sys
import re
import subprocess
import argparse
import json

version = "0.2"
ada2lovelace = 1000000

def getconfig(configfile):
    with open(configfile) as f:
        data = json.load(f)
    return data;

def do_pool_cert(config,magic,debug):
    command = 'cardano-cli stake-pool registration-certificate \ \n'
    command = command + '\t--cold-verification-key-file ' + config['nodeVKey'] + ' \ \n'
    command = command + '\t--vrf-verification-key-file ' + config['VRFVKey']  + ' \ \n'
    command = command + '\t--pool-pledge ' + str(config['poolPledge']*ada2lovelace) + ' \ \n'
    command = command + '\t--pool-cost ' + str(config['poolCost']*ada2lovelace)+ ' \ \n'
    command = command + '\t--pool-margin ' + str(config['poolMargin']) + ' \ \n'
    command = command + '\t--pool-reward-account-verification-key-file ' + config['stakeVKey'] + ' \ \n'
    command = command + '\t--pool-owner-stake-verification-key-file ' + config['stakeVKey'] + ' \ \n'
    command = command + '\t' + magic + ' \ \n'
    command = command + '\t--single-host-pool-relay <dns based relay, example ~ relaynode1.myadapoolnamerocks.com> \ \n'
    command = command + '\t--pool-relay-port 6000 \ \n'
    command = command + '\t--metadata-url ' + config['metaDataURL'] + ' \ \n'
    command = command + '\t--metadata-hash ' + config['metaDataHash'] + ' \ \n'
    command = command + '\t--out-file pool.cert'
    if debug:
        print(command)
    return command

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

parser = argparse.ArgumentParser(description="generates a script to produce a pool.cert and a transaction to register pool.cert")
#parser.add_argument("-tx", "--transaction", type=str, nargs='?', metavar="payment_address", help="generate a transaction using payment_address")
parser.add_argument("-tx", "--transaction", type=str, metavar="ADDRESS", help="generate a transaction using ADDRESS as payment adress")
parser.add_argument("-g", "--generate", type=str, metavar="FILE", nargs='?', help="generate shell script into FILE", default="reg_cert.sh")
parser.add_argument("-c", "--config", type=str, nargs='?', help="path to config file in json format", default="poolParameter.json")
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

if args.testnet_magic:
    magic = ["--testnet-magic", str(args.testnet_magic)]
    magic_param = "--testnet-magic " + str(args.testnet_magic)
else:
    magic = ["--mainnet"]
    magic_param = "--mainnet"

if args.config and args.generate and not args.transaction:
   my_config = getconfig(args.config)
   do_pool_cert(my_config,magic_param,print_debug)
   sys.exit()

if args.transaction:
    payment_address = args.transaction
    print(payment_address)
    print(magic_param)
    sys.exit()
    ignore = do_query("protocol-parameters","",magic,print_debug)
    tip = json.loads(do_query("tip","",magic,print_debug))

    if float(tip['syncProgress']) < 100.0:
        print("ERROR: node not in sync, please wait until sync process has been finished")
        sys.exit()

    current_slot = int(tip['slot'])

    all_utxo = do_query("utxo",payment,magic,print_debug).splitlines()
    skip_header = 0
    balance = 0
    tx_in = ""
    tx_count = 0

    tx_in = []
    for utxo in all_utxo:
        if (skip_header < 2):
         skip_header = skip_header + 1
        else:
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
#    print("sending " + str(amount) + " lovelace and a fee of " + str(fee) + " lovelace")
#    print("from " + src)
#    print("to   " + dest)
    if args.testnet_magic:
        print("on testnet with magic = " + str(args.testnet_magic))
    else:
        print("on mainnet")

    ignore = do_transaction_raw(tx_in,src + "+" + str(tx_out),dest + "+" + str(amount),str(current_slot + 10000),str(fee),print_debug)
