# stakepool_python_tools
some tools written in python to run cardano staking pools

As a starter an alternative to topologyUpdater.sh is provided. It does not have the full functionality, but will be improved over time. However, it does provide the main functionality by pushing node alive to the Topology Updater API and fetches a new topology file.

The current version supports the same command line options as the shell script. In addition it reads a config json file as shown in the example. All important parameters are supplied by the config file. I.e., there's no additional editing of the python script necessary.

There's no env file and no automatic update of the script itself. Next step is enhancing error handling - like checking config file contents. The script works as it is with no guarantees whatsoever. Please, use it with care!

Future updates will include sending emails for the purpose of monitoring the updates.

If you like the tools - then please support us and stake with ATAAT.
