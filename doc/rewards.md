## claim rewards 

Synopsis of rewards.py:

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
    --signing-key-file <payment.skey> \
    --signing-key-file <stake.skey> \
    --mainnet \
    --out-file tx.signed
```

The command to submit the transaction is:

```shell
cardano-cli transaction submit \
    --tx-file tx.signed \
    --mainnet
```


## support development

If you have any questions then please [send me an email](mailto:askJoe@adapool.at).

If you like the tools provided here - then please support us and stake with ADAAT.
