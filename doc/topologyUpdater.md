# stakepool_python_tools
Some tools written in python to manage Cardano stake pools.

## topology updater

As a starter, an alternative to topologyUpdater.sh is provided. It does exactly the same thing as the original, just with some simpler configuration options.

The current version supports the same command line options as the shell script. In addition it reads a config json file as shown in the example. All important parameters are supplied by the config file. I.e., there's no additional editing of the python script necessary. All exceptions are checked and - if configured - sent over to an admin account for monitoring. Also the returncodes from www.clio.one are checked and in case of an error an email will be sent.

A working smtp server is necessary in order for emails to arrive at the destination email.

There's no env file and no automatic update of the script itself. The script works as it is with no guarantees whatsoever. Please, use it with care!

## check balance and generate transactions

Two additional tools, balance.py and tx.py, implement displaying of the balance of an address (not a complete wallet) and simple transactions. 

This is the synopsis of balance.py:

```
usage: balance.py [-h] [-t [TESTNET_MAGIC]] [-d] [-v] address

query balance for a given address

positional arguments:
  address               the address

optional arguments:
  -h, --help            show this help message and exit
  -t [TESTNET_MAGIC], --testnet-magic [TESTNET_MAGIC]
                        run on testnet with magic number
  -d, --debug           prints debugging information
  -v, --version         show program's version number and exit
```

and tx.py

```
usage: tx.py [-h] [-t [TESTNET_MAGIC]] [-d] [-v] amount source destination

build a transaction for signing with your keys

positional arguments:
  amount                the amount of the transaction in ADA
  source                the source address
  destination           the destination address

optional arguments:
  -h, --help            show this help message and exit
  -t [TESTNET_MAGIC], --testnet-magic [TESTNET_MAGIC]
                        run on testnet with magic number
  -d, --debug           prints debugging information
  -v, --version         show program's version number and exit

```

tx.py is desinged for pool operators and creates a tx.draft file. I.e., the transation must be signed (ideally on an air gapped system) and submitted. The command
to sign the transaction is:

```
cardano-cli transaction sign \
    --tx-body-file tx.draft \
    --signing-key-file payment.skey \
    --mainnet \
    --out-file tx.signed
```

The command to submit the transaction is:

```shell
cardano-cli transaction submit \
    --tx-file tx.signed \
    --mainnet
```

These additional scripts use cardano-cli and therefore a complete node running in the background is required.

## claim rewards 

Let's start with rewards.py:

```
usage: rewards.py [-h] [-t [TESTNET_MAGIC]] [-d] [-v] stake_address dest_address

build a transaction for signing with your keys

positional arguments:
  stake_address         the stake address
  dest_address          the destination address

optional arguments:
  -h, --help            show this help message and exit
  -t [TESTNET_MAGIC], --testnet-magic [TESTNET_MAGIC]
                        run on testnet with magic number
  -d, --debug           prints debugging information
  -v, --version         show program's version number and exit
```

A simple example calling rewards.py would look like:

```python
rewards.py $(cat stake.addr) $(cat payment.addr)
```

rewards.py is desinged for pool operators and creates a tx.draft file. I.e., the transation must be signed (ideally on an air gapped system) and submitted. 
The command to sign the transaction is:

```shell
cardano-cli transaction sign \
    --tx-body-file tx.draft \
    --signing-key-file payment.skey \
    --signing-key-file stake.skey \
    --mainnet \
    --out-file tx.signed
```

The command to submit the transaction is:

```shell
cardano-cli transaction submit \
    --tx-file tx.signed \
    --mainnet
```
## change parameters of your pool

Managing pool parameters require multiple steps. First you need a configuration file like the following one (poolParams.json is included here):

```JSON
{
    "nodeVKey":      "node.vkey",       # the path to the node.vkey file
    "VRFVKey":       "vrf.vkey",        # the path to the vrf.vkey file
    "poolPledge":    1000,              # the pool pledge in ADA (not in lovelace!)
    "poolCost":      345,               # the fixed cost also in ADA
    "poolMargin":    2,                 # the margin in percent (you can use 0.75 as well)
    "stakeVKey":     "stake.vkey",      # the path to stake.vkey
    "poolRelays": [                     # the relays - this is optional, but is makes sense to include at least one relay
    	{
	   "name": "<Relay DNS name>",        # a relay using a DNS name
	   "port": 6000
	},
	{
	  "addr": "192.168.10.20",            # a relay using an ipv4 address
	  "port": 6001
	},
	{
	  "addr": "fe80::250:56ff:fe41:a235", # a relay using an ipv6 address
	  "port": 6002
	}
    ],
    "metaDataURL":   "<meta data URL>",   # the URL to your pools meta data information
    "metaDataHash":  "<meta data hash>",  # the hash code generated for your meta data
    "poolCert": "pool.cert",		  # the path for the pool.cert
    "delegCert": "deleg.cert"		  # the path for the deleg.cert

}

```

With the next step you can generate a script to generate the pool.cert with

```python
poolParameter.py -c poolParameter.json -g reg-cert.sh
```
You can use the generated script reg-cert.sh on your air gapped machine to generate the pool.cert. With your new pool.cert file you can then generate a
transaction with

```python
poolParameter.py -tx $(cat payment.addr)
```

After signing the transaction on your air gapped machine with

```shell
cardano-cli transaction sign \
    --tx-body-file tx.draft \
    --signing-key-file payment.skey \
    --signing-key-file node.skey \
    --signing-key-file stake.skey \
    --mainnet \
    --out-file tx.signed
```

you can submit the transaction with

```shell
cardano-cli transaction submit \
    --tx-file tx.signed \
    --mainnet
```
That's it. Your new setup is online. Please note that you'll also have to have your delegation certificate together with your pool certificate in the given
directory when generating the transaction.


## support development

If you have any questions then please [send me an email](mailto:askJoe@adapool.at).

If you like the tools provided here - then please support us and stake with ADAAT.
