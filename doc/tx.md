
## simple transactions

tx.py prepares a draft file for a simple transaction. 

This is the synopsis of tx.py:

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
    --signing-key-file <payment.skey> \
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


## support development

If you have any questions then please [send me an email](mailto:askJoe@adapool.at).

If you like the tools provided here - then please support us and stake with ADAAT.
