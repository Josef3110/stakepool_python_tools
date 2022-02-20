## sentip

sendtip.py is a tool to send tip information to pooltool.io. SPO's can compare their pools performance with other pools also sending tip. Usually, this is done via cncli, but this requires a fully synced cncli database. As an alternative some shell scripts can be used. Still this implementation in python offers a bit more flexibility. One can use the pooltool.json configuration file from cncli or using the command line to set the parameters.

This is the synopsis of sendtip.py:

```
usage: sendtip.py [-h] [-a [APIKEY]] [-p [POOLID]] [-c [CONFIG]] [-t [TESTNET_MAGIC]] [-d] [-v]

sendtip for pooltool.io

options:
  -h, --help            show this help message and exit
  -a [APIKEY], --apiKey [APIKEY]
                        API key from pooltool.io
  -p [POOLID], --poolId [POOLID]
                        pool ID
  -c [CONFIG], --config [CONFIG]
                        path to config file in json format
  -t [TESTNET_MAGIC], --testnet-magic [TESTNET_MAGIC]
                        run on testnet with magic number
  -d, --debug           prints debugging information
  -v, --version         show program's version number and exit

```

Like with cncli, an example for a systemd service can be found in ../service/sendtip.service.

## support development

If you have any questions then please [send me an email](mailto:askJoe@adapool.at).

If you like the tools provided here - then please support us and stake with ADAAT.
