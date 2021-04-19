#!/usr/bin/python3
#
# topologyUpdater as python variant

import sys
import argparse
import requests
import json
import time
from datetime import datetime

# define some constants upfront

cnode_valency = "1"
max_peers = "15"
nwmagic = "764824073"       # network magic for mainnet - if you want a testnet then change the value in config file instead

def getconfig(configfile):
    with open(configfile) as f:
        data = json.load(f)
        f.close()
    return data;

def requestmetric(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S") + " Http Error: " + repr(errh))
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S") + " Error Connecting: " + repr(errc))
        sys.exit()
    except requests.exceptions.Timeout as errt:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S") + " Timeout Error: " + repr(errt))
        sys.exit()
    except requests.exceptions.RequestException as err:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S") + " OOps: Something Else " + repr(err))
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

if args.version:
    print("topologyUpdater.py version 0.3")
    sys.exit()

if args.config:
    my_config = getconfig(args.config)
    cnode_hostname = my_config['hostname']
    cnode_port = my_config['port']
    cnode_valency = my_config['valency']
    max_peers = my_config['maxPeers']
    destination_topology_file = my_config['destinationTopologyFile']
    logfile = my_config['logfile']
    nwmagic = my_config['networkMagic']

if args.push:
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
    url = url + "&magic=" + nwmagic + "&" + cnode_hostname 

    response = requests.get(url)
    print(response.text)
    log = open(logfile, "a")
    n = log.write(response.text)
    log.close()

    # check resultcode

    #parsed_response = json.loads(response.text)
    #if (parsed_response['resultcode'] != '204'):
    #    print("got resultcode = " + parsed_response['resultcode'])

if args.fetch:
    url = "https://api.clio.one/htopology/v1/fetch/?max=" + max_peers + "&magic=" + nwmagic
    response = requests.get(url)
    parsed_response = json.loads(response.text)
    if (parsed_response['resultcode'] != '201'):
        print("got wrong resultcode = " + parsed_response['resultcode'])
        sys.exit()

    # now we have to add custom peers

    for peer in my_config['customPeers']:
        parsed_response['Producers'].append(peer)

    # write topology to file

    topology_file = open(destination_topology_file, "wt")
    n = topology_file.write(json.dumps(parsed_response, indent=4))
    topology_file.close()
