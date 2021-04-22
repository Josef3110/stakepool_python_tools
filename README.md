# stakepool_python_tools
some tools written in python to run cardano staking pools

As a starter, an alternative to topologyUpdater.sh is provided. It does exactly the same thing as the original, just with some simpler configuration options.

The current version supports the same command line options as the shell script. In addition it reads a config json file as shown in the example. All important parameters are supplied by the config file. I.e., there's no additional editing of the python script necessary. All exceptions are checked and - if configured - sent over to an admin account for monitoring. Also the returncodes from www.clio.one are checked and in case of an error an email will be sent.

A working smtp server is necessary in order for emails to arrive at the destination email.

There's no env file and no automatic update of the script itself. The script works as it is with no guarantees whatsoever. Please, use it with care!

If you like the tools provided here - then please support us and stake with ATAAT.
