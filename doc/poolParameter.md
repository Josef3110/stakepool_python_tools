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
    --signing-key-file <payment.skey> \
    --signing-key-file <node.skey> \
    --signing-key-file <stake.skey> \
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
