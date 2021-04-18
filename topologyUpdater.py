#!/usr/bin/python3
#
# topologyUpdater as python variant

import sys
import requests
import json
import time
from datetime import datetime

# define some constants upfront
# TODO: try to get ip address from the system or some configuration file

# for the moment configuration is pretty much like the shell script by changing values beloq

cnode_hostname = "the hostname"     # insert your hostname or ip address
cnode_port = "3001"                 # insert your port number
cnode_valency = "1"
max_peers = "15"
custom_peers = "75.119.131.17:5002:1"
destination_topology_file = "mainnet-topology.json"
logfile = "logs/topologyUpdater_lastresult.json"
mainnet_nwmagic = "764824073"

# ------ nothing to chage below this line ----------------

def getpeers(current_peers):
    peers_list = custom_peers.split(',')
    for element in peers_list:
        peer = element.split(':')
        if len(peer) == 3:
            new_peer = '{ "addr" : "' + peer[0] + '",  "port" : "' + peer[1] + '", "valency" : "' + peer[2] + '" }'
            new_peer_json = json.loads(new_peer)
            current_peers['Producers'].append(new_peer_json)
        else:
            print("custom peer: " + element + " has wrong format")
            sys.exit()
    return current_peers;

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
url = url + "&magic=" + mainnet_nwmagic + "&" + cnode_hostname 

response = requests.get(url)
print(response.text)
log = open(logfile, "a")
n = log.write(response.text)
log.close()

# check resultcode

#parsed_response = json.loads(response.text)
#if (parsed_response['resultcode'] != '204'):
#    print("got resultcode = " + parsed_response['resultcode'])

url = "https://api.clio.one/htopology/v1/fetch/?max=" + max_peers + "&magic=" + mainnet_nwmagic
response = requests.get(url)
parsed_response = json.loads(response.text)
if (parsed_response['resultcode'] != '201'):
    print("got wrong resultcode = " + parse_dresponse['resultcode'])
    sys.exit()

# now we have to add custom peers

my_new_peers = getpeers(parsed_response)

# write topology to file

topology_file = open(destination_topology_file, "wt")
n = topology_file.write(json.dumps(my_new_peers, indent=4))
topology_file.close()
