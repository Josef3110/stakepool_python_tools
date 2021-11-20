#!/usr/bin/python3
#
# topologyUpdater as python variant

import os
import sys
import argparse
import requests
import json
import time
import smtplib
import email.utils
from email.mime.text import MIMEText
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from datetime import datetime

version = "0.8"

# define some default values upfront

cnode_valency_default = "1"
ipVersion_default = "4"             # other possible values are "6" or "mix"
max_peers_default = "15"
nwmagic_default = "764824073"       # network magic for mainnet - if you want a testnet then change the value in config file instead
metricsURL_default = "http://localhost:12798/metrics"

def timestamp4log():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S");

def sendmail(email_config,message):
    ts_message = os.path.basename(sys.argv[0]) + "@" + timestamp4log() + ": " + message
    if not bool(email_config):
        print(ts_message)
    else:
        msg = MIMEText(ts_message)
        msg['To'] = email.utils.formataddr(('Admin', email_config['msgTo']))
        msg['From'] = email.utils.formataddr(('Monitoring', email_config['msgFrom']))
        msg['Subject'] = email_config['msgSubject']
        server = smtplib.SMTP(email_config['smtpServer'], email_config['smtpPort'])
        #server.set_debuglevel(True) # show communication with the server
        try:
            server.sendmail(email_config['msgFrom'], [email_config['msgTo']], msg.as_string())
        finally:
            server.quit()
    return;

def exception_handler(exception_type, exception, traceback):
    # All your trace are belong to us!
    # your format
    sendmail(ec, exception_type.__name__ + ", " + str(exception))

def allowed_gai_family() -> socket.AddressFamily:
    family = socket.AF_INET
    return family;

def getconfig(configfile):
    with open(configfile) as f:
        data = json.load(f)
    return data;

def requestmetric(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        sendmail(ec, "Http Error: " + repr(errh))
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        sendmail(ec,+ "Error Connecting: " + repr(errc))
        sys.exit()
    except requests.exceptions.Timeout as errt:
        sendmail(ec, + "Timeout Error: " + repr(errt))
        sys.exit()
    except requests.exceptions.RequestException as err:
        sendmail(ec, + "OOps: Something Else " + repr(err))
        sys.exit()
    finally:
        return response;

# main

ec = {}
sys.excepthook = exception_handler

# start with parsing arguments

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fetch", help="only fetch of a fresh topology file", action="store_true")
parser.add_argument("-p", "--push", help="only node alive push to Topology Updater API", action="store_true")
parser.add_argument("-v", "--version", help="displays version and exits", action="store_true")
parser.add_argument("-c", "--config", help="path to config file in json format", default="topologyUpdater.json")

args = parser.parse_args()
myname = os.path.basename(sys.argv[0])

if args.version:
    print(myname + " version " + version)
    sys.exit()

if not args.push and not args.fetch:
    do_both = True
else:
    do_both = False

if args.config:
    my_config = getconfig(args.config)
    if 'email' in my_config:
       ec = my_config['email'] 
    if 'hostname' in my_config:
        cnode_hostname = my_config['hostname']
    else:
        sendmail(ec,"relay hostname parameter is missing in configuration")
        sys.exit()
    if 'port' in my_config:
        cnode_port = my_config['port']
    else:
        sendmail(ec,"relay port parameter is missing in configuration")
        sys.exit()
    if 'valency' in my_config:
        cnode_valency = my_config['valency']
    else:
        cnode_valency = cnode_valency_default
    if 'ipVersion' in my_config:
        ipVersion = my_config['ipVersion']
    else:
        ipVersion = ipVersion_default
    if 'maxPeers' in my_config:
        max_peers = my_config['maxPeers']
    else:
        max_peers = max_peers_default
    if 'metricsURL' in my_config:
        metricsURL = my_config['metricsURL']
    else:
        metricsURL = metricsURL_default
    if 'destinationTopologyFile' in my_config:
        destination_topology_file = my_config['destinationTopologyFile']
    else:
        sendmail(ec,"destination for topology file is missing in configuration")
        sys.exit()
    if 'logfile' in my_config:
        logfile = my_config['logfile']
    else:
        sendmail(ec,"path for logfile is missing in configuration")
        sys.exit()
    if 'networkMagic' in my_config:
        nwmagic = my_config['networkMagic']
    else:
        nwmagic = nwmagic_default

# force to use ipv4 for version 4 configuration

if ipVersion == "4":
    urllib3_cn.allowed_gai_family = allowed_gai_family

if args.push or do_both:
    # first get last block number
    response = requestmetric(metricsURL)

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

    ok_responses = [ '201', '203', '204' ]
    parsed_response = json.loads(response.text)
    if (parsed_response['resultcode'] not in ok_responses):        # add 201 and 203 because those are starting codes
        sendmail(ec, "got bad resultcode = " + parsed_response['resultcode'] + " for push command")

if args.fetch or do_both:
    url = "https://api.clio.one/htopology/v1/fetch/?max=" + max_peers + "&magic=" + nwmagic + "&ipv=" + ipVersion
    response = requests.get(url)
    parsed_response = json.loads(response.text)
    if (parsed_response['resultcode'] != '201'):
        sendmail(ec, "got bad resultcode = " + parsed_response['resultcode'] + " for fetch command")
        sys.exit()

    # now we have to add custom peers

    for peer in my_config['customPeers']:
        parsed_response['Producers'].append(peer)

    # write topology to file

    topology_file = open(destination_topology_file, "wt")
    n = topology_file.write(json.dumps(parsed_response, indent=4))
    topology_file.close()
