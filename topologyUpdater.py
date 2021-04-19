#!/usr/bin/python3
#
# topologyUpdater as python variant

import os
import sys
import argparse
import requests
import json
import time
from datetime import datetime

# define some constants upfront

cnode_valency_default = "1"
max_peers_default = "15"
nwmagic_default = "764824073"       # network magic for mainnet - if you want a testnet then change the value in config file instead

def timestamp4log():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S");

def exception_handler(exception_type, exception, traceback):
    # All your trace are belong to us!
    # your format
    print(os.path.basename(sys.argv[0]) + "@" + timestamp4log() + ": " + exception_type.__name__, exception)

sys.excepthook = exception_handler

def getconfig(configfile):
    with open(configfile) as f:
        data = json.load(f)
    return data;

def requestmetric(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(timestamp4log() + ": Http Error: " + repr(errh))
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        print(timestamp4log() + ": Error Connecting: " + repr(errc))
        sys.exit()
    except requests.exceptions.Timeout as errt:
        print(timestamp4log() + ": Timeout Error: " + repr(errt))
        sys.exit()
    except requests.exceptions.RequestException as err:
        print(timestamp4log() + ": OOps: Something Else " + repr(err))
        sys.exit()
    finally:
        return response;

# main

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fetch", help="only fetch of a fresh topology file", action="store_true")
parser.add_argument("-p", "--push", help="only node alive push to Topology Updater API", action="store_true")
parser.add_argument("-v", "--version", help="displays version and exits", action="store_true")
parser.add_argument("-c", "--config", help="path to config file in json format", default="topologyUpdater.json")

args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.version:
    print(myname + " version 0.5")
    sys.exit()

if not args.push and not args.fetch:
    do_both = True
else:
    do_both = False

if args.config:
    my_config = getconfig(args.config)
    if 'hostname' in my_config:
        cnode_hostname = my_config['hostname']
    else:
        print(myname + "@" + timestamp4log() + ": relay hostname parameter is missing in configuration")
        sys.exit()
    if 'port' in my_config:
        cnode_port = my_config['port']
    else:
        print(myname + "@" + timestamp4log() + ": relay port parameter is missing in configuration")
        sys.exit()
    if 'valency' in my_config:
        cnode_valency = my_config['valency']
    else:
        cnode_valency = cnode_valency_default
    if 'maxPeers' in my_config:
        max_peers = my_config['maxPeers']
    else:
        max_peers = max_peers_default
    if 'destinationTopologyFile' in my_config:
        destination_topology_file = my_config['destinationTopologyFile']
    else:
        print(myname + "@" + timestamp4log() + ": destination for topology file is missing in configuration")
        sys.exit()
    if 'logfile' in my_config:
        logfile = my_config['logfile']
    else:
        print(myname + "@" + timestamp4log() + ": path for logfile is missing in configuration")
        sys.exit()
    if 'networkMagic' in my_config:
        nwmagic = my_config['networkMagic']
    else:
        nwmagic = nwmagic_default

if args.push or do_both:
    # first get last block number
    response = requestmetric('http://localhost:12798/metrics')

    response_list = response.text.splitlines(True)
    metrics = {}
    for element in response_list:
        metric = element.rstrip('\n').split()
        metrics[metric[0]] = metric[1]

    block_number = metrics['cardano_node_metrics_blockNum_int']

    # now register with central

    url = "https://api.clio.one/htopology/v1/?port=" + cnode_port + "&blockNo=" + block_number + "&valency=" + cnode_valency 
    url = url + "&magic=" + nwmagic + "&hostname=" + cnode_hostname 

    response = requests.get(url)
    print(response.text)
    log = open(logfile, "a")
    n = log.write(response.text)
    log.close()

    # check resultcode

    #parsed_response = json.loads(response.text)
    #if (parsed_response['resultcode'] != '204'):
    #    print("got resultcode = " + parsed_response['resultcode'])

if args.fetch or do_both:
    url = "https://api.clio.one/htopology/v1/fetch/?max=" + max_peers + "&magic=" + nwmagic + "&ipv=4"
    response = requests.get(url)
    parsed_response = json.loads(response.text)
    if (parsed_response['resultcode'] != '201'):
        print(myname + "@" + timestamp4log() + ": got wrong resultcode = " + parsed_response['resultcode'])
        sys.exit()

    # now we have to add custom peers

    for peer in my_config['customPeers']:
        parsed_response['Producers'].append(peer)

    # write topology to file

    topology_file = open(destination_topology_file, "wt")
    n = topology_file.write(json.dumps(parsed_response, indent=4))
    topology_file.close()
