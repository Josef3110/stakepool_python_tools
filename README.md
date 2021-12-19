# stakepool_python_tools
Some tools written in python to run cardano staking pools.

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

Tx.py is desinged for pool operators and creates a tx.draft file. I.e., the transation must be signed (ideally on an air gapped system) and submitted. The command
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

## claim rewards and change parameters of your pool

... tbd ...

## support development

If you have any questions then please [send me an email](mailto:askJoe@adapool.at).

If you like the tools provided here - then please support us and stake with ADAAT.
